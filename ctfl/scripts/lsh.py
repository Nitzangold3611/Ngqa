import sys,zipfile
from lxml import etree
from extract import *
z=zipfile.ZipFile(sys.argv[1]);o=order(z)
for i in [int(x) for x in sys.argv[2].split(',')]:
    t=etree.fromstring(z.read('ppt/'+o[i-1]));print('==',i)
    for el in t.find('.//'+P+'spTree'):
        nv=el.find('.//'+P+'cNvPr')
        if nv is None: continue
        print(' ',etree.QName(el).localname,(nv.get('name') or '')[:22],[round(v,2) for v in (box(el) or [])],text(el)[:70].replace('\n','/'))
