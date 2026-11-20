import zipfile,re,sys
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
def order(z):
    rels=z.read('ppt/_rels/presentation.xml.rels').decode()
    m={}
    for r in re.findall(r'<Relationship [^>]*>',rels):
        i=re.search(r'Id="([^"]+)"',r).group(1); t=re.search(r'Target="([^"]+)"',r).group(1); m[i]=t
    return [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"',z.read('ppt/presentation.xml').decode())]
for n in range(1,7):
    z=zipfile.ZipFile(f'd{n}_fix3.pptx'); o=order(z); hits=[]
    for i,s in enumerate(o,1):
        t=etree.fromstring(z.read('ppt/'+s))
        txt=' '.join(t.xpath('//a:t/text()',namespaces={'a':A[1:-1]}))
        if re.search(r'שאל(ה|ות)\s+ל?דוגמ',txt): hits.append((i,txt[:60]))
    print(n,len(o),len(hits)); [print('   ',h) for h in hits]
