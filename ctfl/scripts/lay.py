# layout primitives for the v2 redesign
import re, copy
from lxml import etree
from PIL import ImageFont

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
NSA = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NSP = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NSR = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
E = 914400
NAVY, TEAL, TEAL_D, ORANGE, BODY, GRAY, TINT = '121133', '14DACD', '0E9F97', 'F38911', '23224A', '7C7B98', 'E8F9F8'
EMPH = '0B8A83'
LINE = 'E2E7EE'
SOFT = 'F4F6FA'
OR_D = 'C96A00'
FONTS = {b: ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf' % ('Bold' if b else 'Regular'), 100) for b in (0, 1)}
HEB = re.compile(r'[֐-׿]')


def emu(v):
    return int(round(v * E))


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


class Ids:
    def __init__(self, start):
        self.n = start

    def __call__(self):
        self.n += 1
        return self.n


# ---------- text measurement ----------
def wlen(s, pt, b):
    return FONTS[1 if b else 0].getlength(s) / 100 * pt / 72


def para_lines(runs, width, pt, scale=1.0):
    """runs: list of (text, bold, relsize). returns number of lines when wrapped greedily"""
    lines = 1
    cur = 0.0
    for txt, b, rs in runs:
        if txt == '\n':
            lines += 1
            cur = 0.0
            continue
        size = pt * rs
        for tok in re.split(r'(\s+)', txt):
            if not tok:
                continue
            w = wlen(tok, size, b) * 1.03
            if tok.isspace():
                cur += w
                continue
            if cur + w > width and cur > 0:
                lines += 1
                cur = w
                while cur > width:  # very long token
                    lines += 1
                    cur -= width
            else:
                cur += w
    return lines


def block_height(paras, width, pt, spacing=0.45, line=1.12):
    """paras: list of dicts with runs (text,bold,relsize) and 'rel' size multiplier and 'indent'"""
    h = 0.0
    for i, p in enumerate(paras):
        rel = p.get('rel', 1.0)
        w = width - p.get('indent', 0)
        n = para_lines(p['mruns'], w, pt * rel)
        h += n * pt * rel * line / 72
        if i:
            h += pt * spacing * p.get('sp', 1.0) / 72
    return h


def fit_size(paras, width, height, maxpt, minpt, spacing=0.45):
    pt = maxpt
    while pt >= minpt:
        if block_height(paras, width, pt, spacing) <= height:
            return pt
        pt -= 0.5
    return None


# ---------- XML builders ----------
def solid(c, alpha=None):
    a = f'<a:alpha val="{alpha}"/>' if alpha is not None else ''
    return f'<a:solidFill><a:srgbClr val="{c}">{a}</a:srgbClr></a:solidFill>'


def sp_xml(ids, name, x, y, w, h, geom='rect', fill=None, line=None, lw=1.0, adj=None, body='', anchor='t',
           ins=(0.08, 0.05, 0.08, 0.05), shadow=False, txbox=False, rot=0, flipH=False, wrap=True, ph=None, alpha=None,
           dash=None):
    sid = ids()
    av = ''.join(f'<a:gd name="{k}" fmla="val {v}"/>' for k, v in (adj or {}).items())
    f = solid(fill, alpha) if fill else '<a:noFill/>'
    if line:
        d = f'<a:prstDash val="{dash}"/>' if dash else ''
        ln = f'<a:ln w="{int(lw * 12700)}">{solid(line)}{d}</a:ln>'
    else:
        ln = '<a:ln><a:noFill/></a:ln>'
    eff = ''
    if shadow:
        eff = ('<a:effectLst><a:outerShdw blurRad="76200" dist="19050" dir="5400000" algn="t" rotWithShape="0">'
               '<a:srgbClr val="121133"><a:alpha val="14000"/></a:srgbClr></a:outerShdw></a:effectLst>')
    r = f' rot="{int(rot * 60000)}"' if rot else ''
    fh = ' flipH="1"' if flipH else ''
    tb = ' txBox="1"' if txbox else ''
    phx = f'<p:ph type="{ph}"/>' if ph else ''
    l, t, rr, b = ins
    wr = '' if wrap else ' wrap="none"'
    if not body:
        body = '<a:p><a:endParaRPr lang="he-IL" sz="1200"/></a:p>'
    return (f'<p:sp xmlns:p="{NSP}" xmlns:a="{NSA}" xmlns:r="{NSR}"><p:nvSpPr><p:cNvPr id="{sid}" name="{esc(name)}"/>'
            f'<p:cNvSpPr{tb}/><p:nvPr>{phx}</p:nvPr></p:nvSpPr>'
            f'<p:spPr><a:xfrm{r}{fh}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{geom}"><a:avLst>{av}</a:avLst></a:prstGeom>{f}{ln}{eff}</p:spPr>'
            f'<p:txBody><a:bodyPr{wr} lIns="{emu(l)}" tIns="{emu(t)}" rIns="{emu(rr)}" bIns="{emu(b)}" rtlCol="0" anchor="{anchor}"><a:normAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')


def pic_xml(ids, rid, x, y, w, h, name='Illustration', descr=''):
    sid = ids()
    return (f'<p:pic xmlns:p="{NSP}" xmlns:a="{NSA}" xmlns:r="{NSR}"><p:nvPicPr><p:cNvPr id="{sid}" name="{name}" descr="{esc(descr)}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


def line_xml(ids, x1, y1, x2, y2, color=LINE, lw=1.0, head=None, tail=None, dash=None, name='Line'):
    sid = ids()
    x, y = min(x1, x2), min(y1, y2)
    w, h = abs(x2 - x1), abs(y2 - y1)
    fh = ' flipH="1"' if x2 < x1 else ''
    fv = ' flipV="1"' if y2 < y1 else ''
    he = f'<a:headEnd type="{head}"/>' if head else ''
    te = f'<a:tailEnd type="{tail}"/>' if tail else ''
    d = f'<a:prstDash val="{dash}"/>' if dash else ''
    return (f'<p:cxnSp xmlns:p="{NSP}" xmlns:a="{NSA}"><p:nvCxnSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr><a:xfrm{fh}{fv}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="{int(lw * 12700)}">{solid(color)}{d}{he}{te}</a:ln></p:spPr></p:cxnSp>')


def simple_para(text, pt, color=BODY, bold=False, algn=None, rtl=None, font='Arial'):
    if rtl is None:
        rtl = bool(HEB.search(text))
    if algn is None:
        algn = 'r' if rtl else 'l'
    b = ' b="1"' if bold else ''
    return (f'<a:p><a:pPr algn="{algn}" rtl="{1 if rtl else 0}"><a:buNone/></a:pPr>'
            f'<a:r><a:rPr lang="he-IL" sz="{int(pt * 100)}"{b} dirty="0">{solid(color)}<a:latin typeface="{font}"/><a:cs typeface="{font}"/></a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r></a:p>')


def frag(xml):
    return etree.fromstring(xml)
