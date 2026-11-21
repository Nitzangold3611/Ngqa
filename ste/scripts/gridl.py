import sys,os
from PIL import Image,ImageDraw
tag=sys.argv[1]; ids=[int(x) for x in sys.argv[2].split(',')]; out=sys.argv[3]
fs=[f'src/{tag}_{i:03d}.jpg' for i in ids if os.path.exists(f'src/{tag}_{i:03d}.jpg')]
W=880; ims=[Image.open(f) for f in fs]; h=round(W*ims[0].height/ims[0].width)
rows=(len(ims)+1)//2; g=Image.new('RGB',(W*2,(h+4)*rows),'white')
for k,im in enumerate(ims):
    g.paste(im.resize((W,h)),((k%2)*W,(k//2)*(h+4)))
    ImageDraw.Draw(g).rectangle([(k%2)*W,(k//2)*(h+4),(k%2)*W+46,(k//2)*(h+4)+22],fill='red')
    ImageDraw.Draw(g).text(((k%2)*W+4,(k//2)*(h+4)+4),fs[k][-7:-4],fill='white')
g.save(out,quality=75)
