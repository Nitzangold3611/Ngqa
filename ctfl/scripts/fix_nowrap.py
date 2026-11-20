import sys,zipfile,json
from lxml import etree
from extract import *
from lay import wlen
n=int(sys.argv[1]); src=sys.argv[2]; dst=sys.argv[3]
z=zipfile.ZipFile(src); parts={k:z.read(k) for k in z.namelist()}; o=order(z)
rep={a:b for a,b,c in json.load(open(f'v2_report_{n}.json'))}
hit=[]
def gscale(sp):
    # cumulative scale from group transforms
    sx=1.0; p=sp.getparent()
    while p is not None and etree.QName(p).localname=='grpSp':
        x=p.find(P+'grpSpPr/'+A+'xfrm')
        if x is not None and x.find(A+'chExt') is not None:
            e=x.find(A+'ext'); c=x.find(A+'chExt')
            if int(c.get('cx')): sx*=int(e.get('cx'))/int(c.get('cx'))
        p=p.getparent()
    return sx
for i,s in enumerate(o,1):
    if rep.get(i)!="restyle" or (n,i) in {(2,65),(2,67),(2,68)}: continue
    nm='ppt/'+s; t=etree.fromstring(parts[nm]); ch=False
    for sp in t.iter(P+'sp'):
        bp=sp.find(P+'txBody/'+A+'bodyPr')
        if bp is None or bp.get('wrap')!='none': continue
        b=box(sp)
        if not b: continue
        w=b[2]*gscale(sp)
        mx=0
        for p in sp.iter(A+'p'):
            L=0
            for r in p.iter(A+'r'):
                rp=r.find(A+'rPr'); sz=int(rp.get('sz'))/100 if rp is not None and rp.get('sz') else 18
                L+=wlen(r.findtext(A+'t') or '',sz,rp is not None and rp.get('b')=='1')
            mx=max(mx,L)
        if mx>w*1.08+0.2 and len(text(sp))>8:
            bp.set('wrap','square'); ch=True; hit.append((i,text(sp)[:30].replace('\n','/'),round(mx,2),round(w,2)))
    if ch: parts[nm]=etree.tostring(t,xml_declaration=True,encoding='UTF-8',standalone=True)
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as zo:
    for k,v in parts.items(): zo.writestr(k,v)
for h in hit: print(n,*h)
