#!/usr/bin/env python3
"""Fix dark text on dark filled shapes. usage: fix_contrast.py in.pptx out.pptx [--dry]"""
import sys, zipfile, re, shutil
from lxml import etree
A='http://schemas.openxmlformats.org/drawingml/2006/main'; P='http://schemas.openxmlformats.org/presentationml/2006/main'
ns={'a':A,'p':P}
src,dst=sys.argv[1],sys.argv[2]; dry='--dry' in sys.argv
z=zipfile.ZipFile(src)
th=z.read('ppt/theme/theme1.xml').decode()
SC={}
for k in ['dk1','lt1','dk2','lt2','accent1','accent2','accent3','accent4','accent5','accent6']:
    m=re.search(rf'<a:{k}>.*?(?:val|lastClr)="([0-9A-Fa-f]{{6}})"',th,re.S); SC[k]=m.group(1)
SC.update(tx1=SC['dk1'],bg1=SC['lt1'],tx2=SC['dk2'],bg2=SC['lt2'])
def lum(h):
    r,g,b=(int(h[i:i+2],16)/255 for i in (0,2,4)); return .2126*r+.7152*g+.0722*b
def col(fill):
    c=fill.find('a:srgbClr',ns)
    if c is not None: v=c.get('val')
    else:
        c=fill.find('a:schemeClr',ns)
        if c is None or c.get('val') not in SC: return None
        v=SC[c.get('val')]
    L=lum(v)
    lm=c.find('a:lumMod',ns); lo=c.find('a:lumOff',ns)
    if lm is not None: L=L*int(lm.get('val'))/100000
    if lo is not None: L=L+int(lo.get('val'))/100000
    return L
out={}; report=[]
order=None
pres=z.read('ppt/presentation.xml').decode();rels=z.read('ppt/_rels/presentation.xml.rels').decode()
m=dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"',rels))
order=['ppt/'+m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',pres)]
for n,name in enumerate(order,1):
    t=etree.fromstring(z.read(name)); ch=0
    for sp in t.iter('{%s}sp'%P):
        f=sp.find('p:spPr/a:solidFill',ns)
        if f is None: continue
        L=col(f)
        if L is None or L>=0.3: continue
        for rp in sp.iterfind('.//p:txBody//a:rPr',ns)+sp.findall('.//p:txBody//a:endParaRPr',ns) if False else list(sp.iterfind('.//p:txBody//a:rPr',ns))+list(sp.iterfind('.//p:txBody//a:endParaRPr',ns)):
            rf=rp.find('a:solidFill',ns)
            if rf is None: continue
            cl=col(rf)
            if cl is not None and cl<0.45:
                for c in list(rf): rf.remove(c)
                etree.SubElement(rf,'{%s}srgbClr'%A).set('val','FFFFFF'); ch+=1
                txt=''.join(sp.itertext()).strip()[:30]
                report.append((n,txt))
    if ch: out[name]=etree.tostring(t,xml_declaration=True,encoding='UTF-8',standalone=True)
seen=set()
for n,txt in report:
    if (n,txt) not in seen: seen.add((n,txt)); print(f'slide {n}: {txt}')
if not dry:
    zo=zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED)
    for i in z.infolist(): zo.writestr(i, out.get(i.filename, z.read(i.filename)))
    zo.close()
