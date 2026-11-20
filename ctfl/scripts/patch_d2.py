import zipfile,re,os,sys,shutil,subprocess,tempfile
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}';E=914400
src,dst=sys.argv[1],sys.argv[2]
w=tempfile.mkdtemp(); zipfile.ZipFile(src).extractall(w)
rels=open(f'{w}/ppt/_rels/presentation.xml.rels').read()
m={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rels)}
order=[m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',open(f'{w}/ppt/presentation.xml').read())]
def pics(n):
    f=f'{w}/ppt/'+order[n-1]; t=etree.parse(f)
    return f,t,[p for p in t.getroot().find('.//'+P+'spTree').findall(P+'pic') if not (p.find('.//'+P+'cNvPr').get('name') or '').startswith(('NGQA','Icon'))]
# slide 39: user-story card -> move to the left margin
f,t,ps=pics(39); o=ps[0].find(P+'spPr/'+A+'xfrm/'+A+'off'); o.set('x',str(int(0.45*E))); t.write(f,xml_declaration=True,encoding='UTF-8',standalone=True)
# slide 147: photo -> 75%, anchored at its bottom-left corner
f,t,ps=pics(147); xf=ps[0].find(P+'spPr/'+A+'xfrm'); o,e=xf.find(A+'off'),xf.find(A+'ext')
cx,cy=int(e.get('cx')),int(e.get('cy')); y=int(o.get('y'))
e.set('cx',str(int(cx*.75))); e.set('cy',str(int(cy*.75))); o.set('y',str(y+cy-int(cy*.75))); o.set('x',str(int(0.45*E)))
t.write(f,xml_declaration=True,encoding='UTF-8',standalone=True)
os.remove(dst) if os.path.exists(dst) else None
subprocess.run(['zip','-qXrDy',os.path.abspath(dst),'.'],cwd=w,check=True); shutil.rmtree(w); print('patched d2')
