import zipfile,re,sys,json
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
def order(z):
    rels=z.read('ppt/_rels/presentation.xml.rels').decode()
    m={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rels)}
    return [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',z.read('ppt/presentation.xml').decode())]
def top_text(t):
    parts=[]
    def walk(el, sx=1, sy=1, ox=0, oy=0):
        for ch in el:
            if ch.tag==P+'grpSp':
                g=ch.find(P+'grpSpPr/'+A+'xfrm')
                if g is not None and g.find(A+'chExt') is not None:
                    kx=int(g.find(A+'ext').get('cx'))/max(1,int(g.find(A+'chExt').get('cx'))); ky=int(g.find(A+'ext').get('cy'))/max(1,int(g.find(A+'chExt').get('cy')))
                    walk(ch, sx*kx, sy*ky, ox+(int(g.find(A+'off').get('x'))-int(g.find(A+'chOff').get('x'))*kx)*sx, oy+(int(g.find(A+'off').get('y'))-int(g.find(A+'chOff').get('y'))*ky)*sy)
                else: walk(ch,sx,sy,ox,oy)
            elif ch.tag==P+'sp':
                ph=ch.find('.//'+P+'ph'); xf=ch.find(P+'spPr/'+A+'xfrm')
                txt=' '.join(''.join(p.itertext()).strip() for p in ch.iter(A+'p')).strip()
                if not txt: continue
                istitle=ph is not None and ph.get('type') in ('title','ctrTitle')
                y=(oy+int(xf.find(A+'off').get('y'))*sy) if xf is not None else (0 if istitle else 9e9)
                if istitle or y<1.25*914400: parts.append((y,txt))
    walk(t.find('.//'+P+'spTree'))
    return [p for _,p in sorted(parts)]
def title_of(t):
    # placeholder title first, else the top-most text near the top of the slide
    for sp in t.iter(P+'sp'):
        ph=sp.find('.//'+P+'ph')
        if ph is not None and ph.get('type') in ('title','ctrTitle'):
            s=' '.join(''.join(p.itertext()).strip() for p in sp.iter(A+'p')).strip()
            if s: return s
    best=None
    for sp in t.iter(P+'sp'):
        xf=sp.find(P+'spPr/'+A+'xfrm')
        txt=' '.join(''.join(p.itertext()).strip() for p in sp.iter(A+'p')).strip()
        if xf is None or not txt: continue
        y=int(xf.find(A+'off').get('y'))
        if y<1.2*914400 and (best is None or y<best[0]): best=(y,txt)
    return best[1] if best else ''
out={}
for n in range(1,7):
    z=zipfile.ZipFile(f'd{n}_final.pptx'); o=order(z); seen={}
    for i,s in enumerate(o,1):
        t=etree.fromstring(z.read('ppt/'+s)); parts=top_text(t)
        tt=re.sub(r'\s+',' ',' '.join(parts))
        m=re.search(r'(?<![\d.])(\d\.\d(?:\.\d+)?)(?![\d.])',tt)
        if m and m.group(1)[0]==str(n) and m.group(1) not in seen:
            name=re.sub(r'\s+',' ',tt.replace(m.group(1),'')).strip(' |-–:')
            seen[m.group(1)]=(i,name)
    out[n]={k:v for k,v in seen.items()}
    print('== deck',n,len(o))
    for k,(i,tt) in sorted(seen.items(),key=lambda kv:[int(x) for x in kv[0].split('.')]): print('  ',k,i,tt[:70])

json.dump(out,open('toc.json','w'),ensure_ascii=False)
