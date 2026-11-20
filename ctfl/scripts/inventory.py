import zipfile,re,json,sys,hashlib,os
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
E=914400
def order(z):
    rels=z.read('ppt/_rels/presentation.xml.rels').decode()
    m={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rels)}
    return [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',z.read('ppt/presentation.xml').decode())]
tot={'slides':0,'pics':0,'tables':0,'charts':0,'smartart':0,'groups':0}
inv={}
for n in range(1,7):
    z=zipfile.ZipFile(f'd{n}_toc.pptx'); o=order(z); deck=[]
    for i,s in enumerate(o,1):
        x=z.read('ppt/'+s); t=etree.fromstring(x)
        rel=z.read('ppt/'+s.replace('slides/','slides/_rels/')+'.rels').decode()
        rm={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rel)}
        tr=t.find('.//'+P+'spTree')
        pics=[];tables=0;charts=0;sa=0;groups=0
        for el in tr.iter(P+'pic'):
            nm=el.find('.//'+P+'cNvPr').get('name') or ''
            if nm.startswith(('NGQA','Icon')): continue
            b=el.find('.//'+A+'blip'); xf=el.find(P+'spPr/'+A+'xfrm')
            tg=rm.get(b.get(R+'embed'),'') if b is not None else ''
            wh=(int(xf.find(A+'ext').get('cx'))/E,int(xf.find(A+'ext').get('cy'))/E) if xf is not None and xf.find(A+'ext') is not None else (0,0)
            pics.append((os.path.basename(tg),round(wh[0],1),round(wh[1],1)))
        for gf in tr.iter(P+'graphicFrame'):
            u=gf.find('.//'+A+'graphicData').get('uri')
            if u.endswith('/table'): tables+=1
            elif u.endswith('/chart'): charts+=1
            elif 'diagram' in u: sa+=1
        groups=len(tr.findall(P+'grpSp'))
        nsp=len([sp for sp in tr.iter(P+'sp') if ''.join(sp.itertext()).strip()])
        deck.append({'i':i,'pics':pics,'tables':tables,'charts':charts,'smartart':sa,'groups':groups,'textshapes':nsp})
        tot['slides']+=1; tot['pics']+=len(pics); tot['tables']+=tables; tot['charts']+=charts; tot['smartart']+=sa; tot['groups']+=groups
    inv[n]=deck
json.dump(inv,open('inventory.json','w'))
print(tot)
for n in inv:
    d=inv[n]; print(n,'slides',len(d),'w/pics',sum(1 for s in d if s['pics']),'pics',sum(len(s['pics']) for s in d),'tables',sum(s['tables'] for s in d),'smartart',sum(s['smartart'] for s in d),'groups',sum(s['groups'] for s in d),'charts',sum(s['charts'] for s in d), 'many-shapes(>6)',sum(1 for s in d if s['textshapes']>6))
