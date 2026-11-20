import zipfile,re,sys,os,io
from PIL import Image
src={1:'GenAI פרק מס 1.pptx',2:'GenAI פרק מס 2.pptx',3:'GenAI פרק מס 3.pptx',4:'GenAI פרק מס 4.pptx',5:'פרק מס 5 GenAI.pptx'}
D='/mnt/user-data/uploads/CT-GenAI/מצגות לקורסים פרטיים/'
for n,f in src.items():
  z=zipfile.ZipFile(D+f);os.makedirs(f'src/ch{n}',exist_ok=True)
  pres=z.read('ppt/presentation.xml').decode();prel=z.read('ppt/_rels/presentation.xml.rels').decode()
  rid2t=dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',prel));rid2t.update({a:b for b,a in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"',prel)})
  order=[rid2t[r] for r in re.findall(r'<p:sldId [^>]*r:id="(rId\d+)"',pres)]
  info=[]
  for i,t in enumerate(order,1):
    s='ppt/'+t;x=z.read(s).decode();rels=z.read(s.replace('slides/','slides/_rels/')+'.rels').decode()
    rm={a:b for a,b in re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',rels)};rm.update({a:b for b,a in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"',rels)})
    best=None
    for rid in re.findall(r'r:embed="(rId\d+)"',x):
      m='ppt/'+rm[rid].replace('../','');im=Image.open(io.BytesIO(z.read(m)))
      if best is None or im.size[0]*im.size[1]>best[1].size[0]*best[1].size[1]:best=(m,im)
    im=best[1].convert('RGB');im.save(f'src/ch{n}/s{i:02d}.jpg',quality=90)
    info.append((i,best[0],im.size, 'hidden' if 'show="0"' in x[:300] else ''))
  print(n,len(order),info[0],[k for k in info if k[3]])
