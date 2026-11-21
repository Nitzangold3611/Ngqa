import sys,glob
from PIL import Image,ImageDraw
tag,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
fs=[f'src/{tag}_{i:03d}.jpg' for i in range(a,b+1)]
W=880
fs=[f for f in fs if __import__('os').path.exists(f)]
ims=[Image.open(f) for f in fs]
h=round(W*ims[0].height/ims[0].width)
cols=2; rows=(len(ims)+1)//2
g=Image.new('RGB',(W*cols,(h+4)*rows),'white')
for k,im in enumerate(ims):
    g.paste(im.resize((W,h)),((k%2)*W,(k//2)*(h+4)))
    ImageDraw.Draw(g).rectangle([(k%2)*W,(k//2)*(h+4),(k%2)*W+46,(k//2)*(h+4)+22],fill='red')
    ImageDraw.Draw(g).text(((k%2)*W+4,(k//2)*(h+4)+4),fs[k][-7:-4],fill='white')
g.save(f'/tmp/g_{tag}_{a}.jpg',quality=72)
print(f'/tmp/g_{tag}_{a}.jpg')
