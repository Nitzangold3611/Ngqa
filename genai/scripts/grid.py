import sys
from PIL import Image,ImageDraw
n=int(sys.argv[1]);a=int(sys.argv[2]);b=int(sys.argv[3]);W=int(sys.argv[4]) if len(sys.argv)>4 else 960
ims=[]
for i in range(a,b+1):
  try:im=Image.open(f'src/ch{n}/s{i:02d}.jpg')
  except:continue
  im=im.resize((W,int(W*im.size[1]/im.size[0])));d=ImageDraw.Draw(im);d.rectangle((0,0,60,30),fill='red');d.text((8,8),str(i),fill='white');ims.append(im)
h=ims[0].size[1];cols=2;rows=(len(ims)+1)//2
o=Image.new('RGB',(W*cols,h*rows),'white')
for k,im in enumerate(ims):o.paste(im,((k%2)*W,(k//2)*h))
o.save('/tmp/g.jpg',quality=88)
