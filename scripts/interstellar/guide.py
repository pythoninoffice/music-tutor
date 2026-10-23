import sys, numpy as np
from PIL import Image, ImageDraw
N='CDEFGAB'
def go(f, tre=None, bas=None):
    im=Image.open(f).convert('RGB'); a=np.asarray(im.convert('L'))<128
    r=a.sum(1); L=[y for y in range(len(r)) if r[y]>a.shape[1]*0.35]
    ls=[];[ls.append(y) for y in L if not ls or y-ls[-1]>3]
    sp=(ls[4]-ls[0])/4/2
    E4=tre if tre else ls[4]; G2=bas if bas else ls[-1]
    d=ImageDraw.Draw(im)
    for base,d0,lo,hi in ((E4,30,-6,16),(G2,18,-6,16)):
        for k in range(lo,hi):
            y=base-k*sp; n=d0+k; nm=N[n%7]+str(n//7)
            col=(255,0,0) if n%7 in (0,) else ((0,150,0) if n%7==5 else (120,120,255))
            if k%2: d.line([0,y,im.width,y],fill=col+(0,),width=1)
            d.text((2+ (k%2)*22,y-6),nm,fill=col)
    im.save(f.replace('.png','_g.png'))
for f in sys.argv[1:]: go(f)
