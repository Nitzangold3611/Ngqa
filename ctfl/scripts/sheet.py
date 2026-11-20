import sys,os,glob
from PIL import Image,ImageDraw
d=sys.argv[1]; pre=sys.argv[2]; per=int(sys.argv[3]) if len(sys.argv)>3 else 20
fs=sorted(glob.glob(f'{d}/s-*.jpg'))
im0=Image.open(fs[0]); w,h=im0.size; cols=4; tw=420; th=int(h*tw/w)
outs=[]
for g in range(0,len(fs),per):
    chunk=fs[g:g+per]; rows=(len(chunk)+cols-1)//cols
    c=Image.new('RGB',(cols*tw,rows*(th+4)),'white'); dr=ImageDraw.Draw(c)
    for k,f in enumerate(chunk):
        im=Image.open(f).resize((tw,th)); x=(k%cols)*tw; y=(k//cols)*(th+4); c.paste(im,(x,y))
        n=int(os.path.basename(f)[2:-4]); dr.rectangle([x,y,x+34,y+18],fill='red'); dr.text((x+3,y+3),str(n),fill='white')
    o=f'{pre}_{g//per}.jpg'; c.save(o,quality=80); outs.append(o)
print(' '.join(outs))
