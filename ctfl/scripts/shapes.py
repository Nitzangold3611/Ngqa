import zipfile,re,sys
from lxml import etree
exec(open('inventory.py').read().split('tot=')[0])
def info(z,s):
    t=etree.fromstring(z.read('ppt/'+s)); tr=t.find('.//'+P+'spTree'); out=[]
    for el in tr:
        tag=etree.QName(el).localname
        if tag in('nvGrpSpPr','grpSpPr'):continue
        nv=el.find('.//'+P+'cNvPr'); nm=nv.get('name') if nv is not None else ''
        ph=el.find('.//'+P+'ph'); pht=(ph.get('type','body')+':'+ph.get('idx','')) if ph is not None else ''
        xf=el.find('.//'+A+'xfrm'); 
        pos=''
        if xf is not None and xf.find(A+'off') is not None:
            o=xf.find(A+'off');e=xf.find(A+'ext');pos='%.2f,%.2f %.2fx%.2f'%(int(o.get('x'))/E,int(o.get('y'))/E,int(e.get('cx'))/E,int(e.get('cy'))/E)
        geom=el.find('.//'+A+'prstGeom'); g=geom.get('prst') if geom is not None else ''
        fill='fill' if el.find(P+'spPr/'+A+'solidFill') is not None else ''
        txt=' | '.join(''.join(p.itertext()) for p in el.iter(A+'p'))[:90]
        out.append(f'{tag:12} {nm[:18]:18} {pht:10} {pos:24} {g:10} {fill:4} {txt}')
    return out
n=int(sys.argv[1]); z=zipfile.ZipFile(f'd{n}_toc.pptx'); o=order(z)
for i in [int(x) for x in sys.argv[2].split(',')]:
    print('== slide',i,o[i-1]); print('\n'.join(info(z,o[i-1])))
