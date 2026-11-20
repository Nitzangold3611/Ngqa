import sys
from PIL import Image
d=sys.argv[1];ids=[int(x) for x in sys.argv[2].split(',')];out=sys.argv[3]
ims=[Image.open(f'{d}/s-%02d.jpg'%i) for i in ids];w,h=ims[0].size
o=Image.new('RGB',(w*2,h*((len(ims)+1)//2)),'white')
for k,im in enumerate(ims):o.paste(im,((k%2)*w,(k//2)*h))
o.save(out,quality=85)
