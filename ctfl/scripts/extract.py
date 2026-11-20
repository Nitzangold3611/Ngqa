import zipfile,re,json,sys,copy
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
E=914400
NUMRE=re.compile(r'^\s*\d+(\.\d+)*\s*$')
def order(z):
    rels=z.read('ppt/_rels/presentation.xml.rels').decode()
    m={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rels)}
    return [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',z.read('ppt/presentation.xml').decode())]
def box(el):
    xf=el.find(P+'spPr/'+A+'xfrm')
    if xf is None: xf=el.find(P+'grpSpPr/'+A+'xfrm')
    if xf is None: xf=el.find(P+'xfrm')
    if xf is None or xf.find(A+'off') is None: return None
    o=xf.find(A+'off');e=xf.find(A+'ext')
    return [int(o.get('x'))/E,int(o.get('y'))/E,int(e.get('cx'))/E,int(e.get('cy'))/E]
def text(el): return '\n'.join(''.join(t.text or '' for t in p.iter(A+'t')) for p in el.iter(A+'p')).strip()
def maxsz(el):
    s=[int(r.get('sz')) for r in el.iter(A+'rPr',A+'endParaRPr') if r.get('sz')]
    return max(s)/100 if s else 0
def kind(el):
    tag=etree.QName(el).localname
    if tag=='sp':
        ph=el.find('.//'+P+'ph')
        if ph is not None and ph.get('type') in('title','ctrTitle'): return 'title'
        sppr=el.find(P+'spPr'); g=sppr.find(A+'prstGeom')
        geom=g.get('prst') if g is not None else ('cust' if sppr.find(A+'custGeom') is not None else 'rect')
        filled=sppr.find(A+'solidFill') is not None or sppr.find(A+'gradFill') is not None or sppr.find(A+'blipFill') is not None
        ln=sppr.find(A+'ln'); lined=ln is not None and ln.find(A+'noFill') is None and len(ln)>0
        style=el.find(P+'style') is not None and not el.find('.//'+P+'cNvSpPr').get('txBox')
        t=text(el)
        if not t: return 'shape'
        if ph is not None and not filled and not lined: return 'textplain'
        if geom=='rect' and not filled and not lined and not style: return 'textplain'
        if geom in('rect','roundRect','snip1Rect','round2SameRect','flowChartProcess','flowChartAlternateProcess') : return 'boxed'
        return 'shapetext'
    return {'pic':'pic','grpSp':'grp','cxnSp':'cxn','graphicFrame':'gf'}.get(tag,tag)
def classify(t):
    tr=t.find('.//'+P+'spTree'); els=[e for e in tr if etree.QName(e).localname not in('nvGrpSpPr','grpSpPr','extLst')]
    title=[];num=[];rest=[]
    for e in els:
        k=kind(e); b=box(e); tx=text(e)
        if k=='pic':
            nm=e.find('.//'+P+'cNvPr').get('name') or ''
            if nm.startswith('Icon'): rest.append(('icon',e)); continue
        if k=='title': title.append(e); continue
        if b and b[1]<0.95 and tx and NUMRE.match(tx) and b[2]<1.6: num.append(e); continue
        if b and b[1]<0.9 and b[3]<1.3 and tx and k in('textplain','grp','boxed') and maxsz(e)>=20: title.append(e); continue
        if k=='sp' or k=='shape':
            if b and b[1]<0.9 and b[3]<0.9 and not tx: title.append(e); continue  # deco bars near title
        if k=='shape' and b and b[1]<0.95 and b[2]<0.4: title.append(e); continue
        rest.append((k,e))
    ks=[k for k,_ in rest]
    if any(k in('grp','gf','cxn','shapetext','shape') for k in ks): cls='complex'
    elif ks.count('boxed')>=3 and ks.count('textplain')<=1 and ks.count('pic')==0: cls='cards'
    elif 'boxed' in ks: cls='complex'
    elif ks.count('textplain')<=3 and ks.count('pic')<=2: cls='simple'
    else: cls='complex'
    return cls,title,num,rest
if __name__=='__main__':
    from collections import Counter
    tot=Counter()
    for n in range(1,7):
        z=zipfile.ZipFile(f'd{n}_toc.pptx'); o=order(z); c=Counter(); lst={}
        for i,s in enumerate(o,1):
            if i<=2: continue
            cls,ti,nu,rest=classify(etree.fromstring(z.read('ppt/'+s))); c[cls]+=1; lst.setdefault(cls,[]).append(i)
        print(n,dict(c)); print('  complex:',lst.get('complex')); print('  cards:',lst.get('cards')); tot+=c
    print(tot)
