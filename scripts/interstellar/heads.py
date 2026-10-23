import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
NAMES='CDEFGAB'
def pname(d):  # diatonic index, C4 = 28
    return NAMES[d%7]+str(d//7)
def run(f):
    a=np.asarray(Image.open(f).convert('L'))<128
    r=a.sum(1); L=[y for y in range(len(r)) if r[y]>a.shape[1]*0.35]
    ls=[];[ls.append(y) for y in L if not ls or y-ls[-1]>3]
    b=a.copy()

    # notehead: open with ellipse-ish kernel to kill stems/beams
    b=nd.binary_fill_holes(b); k=np.ones((6,6),bool)
    o=nd.binary_opening(b,structure=k)
    lab,n=nd.label(o); out=[]
    for s in nd.find_objects(lab):
        h=s[0].stop-s[0].start; w=s[1].stop-s[1].start
        if 11<=h<=21 and 11<=w<=26:
            out.append(((s[1].start+s[1].stop)/2,(s[0].start+s[0].stop)/2))
    print(f,'lines',ls)
    t=ls[:5]; sp=(t[4]-t[0])/8; last=ls[-1]; bb=[last-8*sp+2*sp*i for i in range(5)]
    for x,y in sorted(out):
        if y<(t[4]+bb[0])/2: d=30+round((t[4]-y)/sp)   # E4=30
        else: d=18+round((bb[4]-y)/sp)                 # G2=18
        print(f'{x:5.0f} {y:5.0f} {pname(d)}')
for f in sys.argv[1:]: run(f)
