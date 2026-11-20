import zipfile,re,os,sys,shutil,subprocess,tempfile
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}';E=914400
src,dst=sys.argv[1],sys.argv[2]
w=tempfile.mkdtemp(); zipfile.ZipFile(src).extractall(w)
rels=open(f'{w}/ppt/_rels/presentation.xml.rels').read()
m={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rels)}
order=[m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',open(f'{w}/ppt/presentation.xml').read())]
# slide 33: keep the SD formula in the left margin, narrow the text block so its lines stop short of it
f=f'{w}/ppt/'+order[32]; t=etree.parse(f)
for sp in t.getroot().iter(P+'sp'):
    txt=''.join(sp.itertext()); xf=sp.find(P+'spPr/'+A+'xfrm')
    if xf is None: continue
    o,e=xf.find(A+'off'),xf.find(A+'ext')
    if txt.strip().startswith('SD = (b'):
        o.set('x',str(int(0.35*E)))
    elif txt.startswith('הערכה של שלוש נקודות'):
        right=int(o.get('x'))+int(e.get('cx')); o.set('x',str(int(2.7*E))); e.set('cx',str(right-int(2.7*E)))
t.write(f,xml_declaration=True,encoding='UTF-8',standalone=True)
os.remove(dst) if os.path.exists(dst) else None
subprocess.run(['zip','-qXrDy',os.path.abspath(dst),'.'],cwd=w,check=True); shutil.rmtree(w); print('patched d5')
