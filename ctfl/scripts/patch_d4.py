import zipfile,re,os,sys,shutil,subprocess,tempfile
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
src,dst=sys.argv[1],sys.argv[2]
w=tempfile.mkdtemp(); zipfile.ZipFile(src).extractall(w)
rels=open(f'{w}/ppt/_rels/presentation.xml.rels').read()
m={re.search(r'Id="([^"]+)"',r).group(1):re.search(r'Target="([^"]+)"',r).group(1) for r in re.findall(r'<Relationship [^>]*>',rels)}
order=[m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',open(f'{w}/ppt/presentation.xml').read())]
# slide 29: the grey formula box -> 18pt so its first line doesn't wrap
f=f'{w}/ppt/'+order[28]; t=etree.parse(f)
for sp in t.getroot().iter(P+'sp'):
    if ''.join(sp.itertext()).startswith('תוצאת הנוסחה'):
        for r in sp.iter(A+'rPr',A+'endParaRPr'):
            if r.get('sz')=='2000': r.set('sz','1800')
t.write(f,xml_declaration=True,encoding='UTF-8',standalone=True)
os.remove(dst) if os.path.exists(dst) else None
subprocess.run(['zip','-qXrDy',os.path.abspath(dst),'.'],cwd=w,check=True); shutil.rmtree(w); print('patched d4')
