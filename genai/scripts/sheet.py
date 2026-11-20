import sys,glob
from PIL import Image,ImageDraw
d=sys.argv[1];a=int(sys.argv[2]);b=int(sys.argv[3]);out=sys.argv[4]
fs=sorted(glob.glob(d+'/s-*.jpg'))[a-1:b]
ims=[Image.open(f) for f in fs];w,h=ims[0].size
o=Image.new('RGB',(w*2,h*((len(ims)+1)//2)),'white')
for k,im in enumerate(ims):o.paste(im,((k%2)*w,(k//2)*h))
o.save(out,quality=85)
