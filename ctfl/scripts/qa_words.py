import zipfile,re,sys
from lxml import etree
from extract import order,A,P
def words(z,s):
    t=etree.fromstring(z.read('ppt/'+s))
    tx=' '.join(x.text or '' for x in t.iter(A+'t'))
    # smartart / diagram data text
    return set(w for w in re.findall(r'[\w֐-׿]{2,}',tx) if not w.isdigit())
def dwords(z,s):
    rel=z.read('ppt/'+s.replace('slides/','slides/_rels/')+'.rels').decode()
    out=set()
    for tg in re.findall(r'Target="\.\./(diagrams/data\d+\.xml|charts/chart\d+\.xml)"',rel):
        tx=' '.join(re.findall(r'<a:t>([^<]*)</a:t>|<c:v>([^<]*)</c:v>',z.read('ppt/'+tg).decode()) and [a or b for a,b in re.findall(r'<a:t>([^<]*)</a:t>|<c:v>([^<]*)</c:v>',z.read('ppt/'+tg).decode())] or [])
        out|=set(w for w in re.findall(r'[\w֐-׿]{2,}',tx) if not w.isdigit())
    return out
for n in range(1,7):
    a=zipfile.ZipFile(f'd{n}_toc_v1.pptx');b=zipfile.ZipFile(f'final_{n}.pptx');oa=order(a);ob=order(b)
    dele=[48] if n==4 else []
    ia=[i for i in range(1,len(oa)+1) if i not in dele]
    for k,i in enumerate(ia,1):
        if k>len(ob): break
        wa=words(a,oa[i-1])|dwords(a,oa[i-1]); wb=words(b,ob[k-1])|dwords(b,ob[k-1])
        miss=wa-wb
        if wa and len(miss)>max(2,0.08*len(wa)):
            print(n,k,f'{len(miss)}/{len(wa)}',' '.join(sorted(miss))[:120])
