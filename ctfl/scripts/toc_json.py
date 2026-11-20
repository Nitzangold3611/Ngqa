import zipfile,re,json
from lxml import etree
from extract import *
out={}
for n in range(1,7):
    z=zipfile.ZipFile(f'final_{n}.pptx');o=order(z)
    t=etree.fromstring(z.read('ppt/'+o[1]))
    rel=z.read('ppt/'+o[1].replace('slides/','slides/_rels/')+'.rels').decode()
    rm={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rel)}
    items=[]
    for sp in t.iter(P+'sp'):
        h=sp.find('.//'+A+'hlinkClick')
        if h is None or h.get(R+'id') not in rm: continue
        tx=re.sub(r'\s+',' ',text(sp)).strip()
        b=box(sp)
        sub=tx.startswith('›')
        tx=tx.lstrip('› ').strip()
        m=re.match(r'^(\d+(?:\.\d+)*)\s+(.*)$',tx)
        num,label=(m.group(1),m.group(2)) if m and not sub else ('',tx)
        items.append({'lvl':2 if sub else 1,'num':num,'label':label,'slide':o.index('slides/'+rm[h.get(R+'id')])+1,'_pos':(round(b[0],1) if b else 0,b[1] if b else 0)})
    # reading order: RTL columns (right col first), then y
    items.sort(key=lambda i:(-i['_pos'][0] if i['lvl']==1 else 0,))
    # simpler: sort by slide index (document order)
    items.sort(key=lambda i:(i['slide'],i['lvl']))
    for i in items: i.pop('_pos')
    out[n]=items
json.dump(out,open('toc_site.json','w'),ensure_ascii=False,indent=0)
for n in out: print(n,len(out[n]),out[n][:3])
