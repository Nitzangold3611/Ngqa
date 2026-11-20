import sys
from PIL import Image
d=sys.argv[1]; ids=[int(x) for x in sys.argv[2].split(',')]; out=sys.argv[3]
ims=[Image.open(f'{d}/s-{i:02d}.jpg') if __import__('os').path.exists(f'{d}/s-{i:02d}.jpg') else Image.open(f'{d}/s-{i:03d}.jpg') for i in ids]
w,h=ims[0].size; s=min(0.4,1400/(w*3)); W,H=int(w*s),int(h*s); cols=3
c=Image.new('RGB',(W*cols,H*((len(ims)+cols-1)//cols)),'white')
for k,im in enumerate(ims): c.paste(im.resize((W,H)),((k%cols)*W,(k//cols)*H))
c.save(out,quality=85)
