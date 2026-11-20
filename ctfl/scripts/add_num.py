import sys,zipfile,re,json
from lxml import etree
from extract import order,P,A
n=int(sys.argv[1]); src=sys.argv[2]; dst=sys.argv[3]
z=zipfile.ZipFile(src); parts={k:z.read(k) for k in z.namelist()}; sl=order(z)
pres=parts['ppt/presentation.xml'].decode()
W=int(re.search(r'sldSz cx="(\d+)"',pres).group(1))/914400
rep={a:b for a,b,c in json.load(open(f'v2_report_{n}.json'))}
tot=len(sl); E=914400
for i,s in enumerate(sl,1):
    nm='ppt/'+s; t=etree.fromstring(parts[nm]); tr=t.find('.//'+P+'spTree')
    for old in [x for x in tr if x.find('.//'+P+'cNvPr') is not None and x.find('.//'+P+'cNvPr').get('name')=='Slide Counter']: tr.remove(old)
    dark = i==1 or rep.get(i)=='cover'
    col='A9B1C2' if dark else '7C7B98'
    mid=max(int(x.get('id')) for x in t.iter(P+'cNvPr') if x.get('id','').isdigit())+1
    x,y,w,h=(0.3,7.1,1.1,0.28) if W>11 else (0.2,7.12,0.95,0.26)
    rp=f'<a:rPr lang="en-US" sz="1000" b="1" dirty="0"><a:solidFill><a:srgbClr val="{col}"/></a:solidFill><a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr>'
    xml=(f'<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
         f'<p:nvSpPr><p:cNvPr id="{mid}" name="Slide Counter"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
         f'<p:spPr><a:xfrm><a:off x="{int(x*E)}" y="{int(y*E)}"/><a:ext cx="{int(w*E)}" cy="{int(h*E)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
         f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"/><a:lstStyle/>'
         f'<a:p><a:pPr algn="l" rtl="0"/><a:fld id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">{rp}<a:t>{i}</a:t></a:fld>'
         f'<a:r>{rp}<a:t>/{tot}</a:t></a:r></a:p></p:txBody></p:sp>')
    tr.append(etree.fromstring(xml))
    parts[nm]=etree.tostring(t,xml_declaration=True,encoding='UTF-8',standalone=True)
with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as zo:
    for k,v in parts.items(): zo.writestr(k,v)
print(n,tot)
