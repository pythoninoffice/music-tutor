# zg.py page x0 y0 x1 y1 out  -- auto-detect treble staff (first 5 lines) in crop, upscale 2x, label every diatonic step
import sys, numpy as np
from PIL import Image, ImageDraw
p,x0,y0,x1,y1,out=sys.argv[1:7]; x0,y0,x1,y1=map(int,(x0,y0,x1,y1))
im=Image.open(f'hp-{p}.png').convert('RGB').crop((x0,y0,x1,y1))
a=np.asarray(im.convert('L'))<128; r=a.sum(1)
def lrun(row):
    m=c=0
    for v in row:
        c=c+1 if v else 0; m=max(m,c)
    return m
best=None
for sx in range(0,a.shape[1]-40,10):
    st=a[:,sx:sx+40].sum(1); Ls=[y for y in range(len(st)) if st[y]>=38]
    q=[];[q.append(y) for y in Ls if not q or y-q[-1]>3]
    if len(q)>=5 and (best is None or len(q)<len(best[1]) or (len(best[1])<5)):
        sp=[q[i+1]-q[i] for i in range(4)]
        if max(sp)-min(sp)<=3 and min(sp)>=12: best=(sx,q); break
L=best[1] if best else []; ls=[]
[ls.append(y) for y in L if not ls or y-ls[-1]>3]
print(ls)
clef=sys.argv[7] if len(sys.argv)>7 else 't'
sp=(ls[4]-ls[0])/8; base=ls[4]; d0=30 if clef=='t' else 18   # E4 or G2 bottom line
im=im.resize((im.width*2,im.height*2)); d=ImageDraw.Draw(im); N='CDEFGAB'
for k in range(-8,22):
    y=2*(base-k*sp); n=d0+k
    if k%2==1: d.line([0,y,im.width,y],fill=(255,180,180),width=1)
    for xx in range(0,im.width,300): d.text((xx+4,y-6),N[n%7]+str(n//7),fill=(220,0,0) if k%2 else (0,0,220))
im.save(out)
