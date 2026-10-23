import json, sys, os; sys.path.insert(0,'/workspace/song4'); import toon_compose as TC
from PIL import Image
J=[]
for O,ks in (('/workspace/blender/p3d/toon_out_s4/',('intro','bar30','bar100')),('/workspace/blender/p3d/toon_out_s4b/',('bar25','bar101'))):
    meta=json.load(open(O+'toon_meta.json'))
    for k in ks:
        n='S4_'+k; TC.compose(n, meta, f'/workspace/song4/still_{k}.png', handp=O+n+'_hand.png'); J.append(k)
ims=[Image.open(f'/workspace/song4/still_{k}.png').crop((0,900,1080,1700)).resize((432,320)) for k in J[1:]]
m=Image.new('RGB',(432*2,640)); [m.paste(im,((i%2)*432,(i//2)*320)) for i,im in enumerate(ims)]; m.save(sys.argv[1])
