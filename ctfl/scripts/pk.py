# patch toolkit: loads relayout's layout functions into a namespace bound to one deck
import re, zipfile, io, os, json, copy
from lxml import etree
import lay
from lay import *
import extract
from extract import order, box, text, classify
import topics
import redraw

SRC = open('/home/claude/work/relayout.py').read()
REGION = SRC[SRC.index('def rels_name'):SRC.index('# ---------------- main')]
KEEP = ('Title', 'Kicker', 'Section Number', 'Title Accent', 'Title Accent 2', 'Slide Counter')


class Deck:
    def __init__(self, n, path):
        self.n = n
        z = zipfile.ZipFile(path)
        self.parts = {k: z.read(k) for k in z.namelist()}
        self.slides = order(z)
        pres = self.parts['ppt/presentation.xml'].decode()
        W = int(re.search(r'sldSz cx="(\d+)"', pres).group(1)) / E
        H = int(re.search(r'sldSz[^>]*cy="(\d+)"', pres).group(1)) / E
        wide = W > 11
        ns = {k: getattr(lay, k) for k in dir(lay) if not k.startswith('__')}
        ns.update(dict(order=order, box=box, text=text, kind=extract.kind, maxsz=extract.maxsz, NUMRE=extract.NUMRE,
                       topic_for=topics.topic_for, redraw=redraw, Image=__import__('PIL.Image').Image, io=io, os=os, re=re,
                       json=json, copy=copy, etree=etree, classify=classify))
        ns.update(dict(N=n, parts=self.parts, slides=self.slides, W=W, H=H, WIDE=wide, ILL='assets/illus',
                       CONTENT=set(), CT=''))
        if wide:
            ns.update(X0=0.55, X1=12.8, Y0=1.28, Y1=6.82, TX0=1.95, TITLE_Y=0.24)
        else:
            ns.update(X0=0.4, X1=9.6, Y0=1.2, Y1=6.85, TX0=1.5, TITLE_Y=0.12)
        exec(REGION, ns)
        self.ns = ns
        self.W, self.H, self.wide = W, H, wide
        self.trees = {}
        self.src = zipfile.ZipFile(f'/home/claude/work/d{n}_toc_v1.pptx')
        self.src_slides = order(self.src)
        self.deleted = []

    def __getattr__(self, k):
        if k.startswith('_'):
            raise AttributeError(k)
        return self.ns[k]

    def tree(self, i):
        if i not in self.trees:
            self.trees[i] = etree.fromstring(self.parts['ppt/' + self.slides[i - 1]])
        return self.trees[i]

    def sptree(self, i):
        return self.tree(i).find('.//' + P + 'spTree')

    def ids(self, i):
        if not hasattr(self, '_ids'):
            self._ids = {}
        if i in self._ids:
            return self._ids[i]
        t = self.tree(i)
        self._ids[i] = Ids(max([int(x.get('id')) for x in t.iter(P + 'cNvPr') if x.get('id', '').isdigit()] or [1]) + 50)
        return self._ids[i]

    def clear(self, i, keep=KEEP):
        tr = self.sptree(i)
        for el in list(tr):
            if etree.QName(el).localname in ('nvGrpSpPr', 'grpSpPr', 'extLst'):
                continue
            nv = el.find('.//' + P + 'cNvPr')
            if nv is not None and (nv.get('name') or '') in keep:
                continue
            tr.remove(el)
        tm = self.tree(i).find(P + 'timing')
        if tm is not None:
            self.tree(i).remove(tm)

    def add(self, i, xmls):
        tr = self.sptree(i)
        for x in xmls:
            if x is None:
                continue
            tr.append(etree.fromstring(x) if isinstance(x, str) else x)

    def find(self, i, name):
        for el in self.tree(i).iter(P + 'sp', P + 'pic', P + 'grpSp', P + 'cxnSp'):
            nv = el.find('.//' + P + 'cNvPr')
            if nv is not None and nv.get('name') == name:
                return el
        return None

    def media(self, i, path_or_bytes, name=None):
        s = self.slides[i - 1]
        if not isinstance(path_or_bytes, bytes):
            return self.add_media(s, path_or_bytes)
        key = 'v2_' + name
        self.parts['ppt/media/' + key] = path_or_bytes
        rn = 'ppt/' + s.replace('slides/', 'slides/_rels/') + '.rels'
        rel = self.parts[rn].decode()
        tgt = '../media/' + key
        m = re.search(r'Id="([^"]+)"[^>]*Target="%s"' % re.escape(tgt), rel)
        if m:
            return m.group(1)
        ids = [int(x) for x in re.findall(r'Id="rId(\d+)"', rel)] or [0]
        rid = 'rId%d' % (max(ids) + 1)
        rel = rel.replace('</Relationships>', f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{tgt}"/></Relationships>')
        self.parts[rn] = rel.encode()
        ext = key.rsplit('.', 1)[-1].lower()
        ct = self.parts['[Content_Types].xml'].decode()
        if f'Extension="{ext}"' not in ct:
            mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif', 'emf': 'image/x-emf', 'wmf': 'image/x-wmf'}.get(ext, 'image/' + ext)
            ct = ct.replace('<Default ', f'<Default Extension="{ext}" ContentType="{mime}"/><Default ', 1)
            self.parts['[Content_Types].xml'] = ct.encode()
        return rid

    def illus(self, i, topic, v=0):
        return self.media(i, f'assets/illus/{topic}_{v}.png')

    # ---- source (v1) access ----
    def stree(self, i):
        return etree.fromstring(self.src.read('ppt/' + self.src_slides[i - 1]))

    def src_image(self, i, pic):
        rel = self.src.read('ppt/' + self.src_slides[i - 1].replace('slides/', 'slides/_rels/') + '.rels').decode()
        rm = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1) for r in re.findall(r'<Relationship [^>]*>', rel)}
        rid = pic.find('.//' + A + 'blip').get(R + 'embed')
        tg = os.path.normpath(os.path.join('ppt/slides', rm[rid])).replace('\\', '/')
        return self.src.read(tg), os.path.basename(tg)

    def copy_src_pic(self, i, pic, x, y, w, h, name='Figure'):
        data, base = self.src_image(i, pic)
        rid = self.media(i, data, f'src{self.n}_{base}')
        try:
            from PIL import Image as I
            im = I.open(io.BytesIO(data))
            iw, ih = im.size
            # account for crop
            sr = pic.find('.//' + A + 'srcRect')
            if sr is not None:
                l, t_, r_, b_ = [int(sr.get(k, 0)) / 100000 for k in ('l', 't', 'r', 'b')]
                iw, ih = iw * (1 - l - r_), ih * (1 - t_ - b_)
        except Exception:
            iw, ih = 4, 3
        a, b, c, d = self.fit_box(x, y, w, h, iw, ih)
        el = etree.fromstring(pic_xml(self.ids(i), rid, a, b, c, d, name))
        sr = pic.find('.//' + A + 'srcRect')
        if sr is not None:
            bf = el.find(P + 'blipFill')
            bf.insert(1, copy.deepcopy(sr))
        return el

    def src_paras(self, i, els):
        return [m for m in self.extract_paras(els) if m]

    def delete(self, i):
        self.deleted.append(i)

    def save(self, path):
        for i, t in self.trees.items():
            self.parts['ppt/' + self.slides[i - 1]] = etree.tostring(t, xml_declaration=True, encoding='UTF-8', standalone=True)
        if self.deleted:
            pres = self.parts['ppt/presentation.xml'].decode()
            rels = self.parts['ppt/_rels/presentation.xml.rels'].decode()
            for i in self.deleted:
                tgt = self.slides[i - 1]
                rid = re.search(r'Id="([^"]+)"[^>]*Target="%s"' % re.escape(tgt), rels) or re.search(r'Target="%s"[^>]*Id="([^"]+)"' % re.escape(tgt), rels)
                rid = rid.group(1)
                pres = re.sub(r'<p:sldId [^>]*r:id="%s"/>' % rid, '', pres)
            self.parts['ppt/presentation.xml'] = pres.encode()
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zo:
            for k, v in self.parts.items():
                zo.writestr(k, v)
