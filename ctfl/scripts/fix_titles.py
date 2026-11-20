#!/usr/bin/env python3
"""Post-process a restyled deck: fit slide titles on one line and fix broken parentheses.
usage: fix_titles.py in.pptx out.pptx"""
import sys, os, re, zipfile, tempfile, shutil, subprocess
from lxml import etree
from PIL import ImageFont

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'a': A, 'p': P, 'r': R}
EMU = 914400
FONT = {False: '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        True: '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'}
_fc = {}

# literal typos in the source text: (pattern, replacement) applied to a paragraph's runs
PAREN_FIXES = [
    (r'(\S+)\)\)$', r'(\1)'),                 # "Debugging))"      -> "(Debugging)"
    (r'\(\(QC', '(QC) '),                      # "((QCמתמקדת"       -> "(QC) מתמקדת"
    (r'\s*(baseline)\)\s*\)', r' (\1)'),       # "baseline) )"      -> "(baseline)"
    (r'\s*(confirmation test)\)\s*\)', r' (\1)'),
    (r'(רציפה)\s+(Continuous integration tools)\) \(', r'\1 (\2) ('),
    (r'(?<!["\w])([A-Za-z][A-Za-z0-9\- ]*?)""', r'"\1"'),   # Scrum"" -> "Scrum"
]


def q(t):
    p, n = t.split(':'); return '{%s}%s' % (NS[p], n)


def font(bold, px):
    k = (bold, px)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT[bold], px)
    return _fc[k]


def text_width_in(s, pt, bold):
    # measure at 100px and scale: width in points -> inches
    f = font(bold, 100)
    return f.getlength(s) / 100 * pt / 72


def load(p):
    return etree.parse(p)


def rels(part):
    d, f = os.path.split(part)
    rp = os.path.join(d, '_rels', f + '.rels')
    if not os.path.exists(rp):
        return {}
    return {r.get('Id'): os.path.normpath(os.path.join(d, r.get('Target'))) for r in load(rp).getroot()}


def ph_of(sp):
    ph = sp.find('.//' + q('p:nvPr') + '/' + q('p:ph'))
    return None if ph is None else (ph.get('type', 'body'), ph.get('idx'))


def find_ph(tree, typ):
    for sp in tree.iter(q('p:sp')):
        p = ph_of(sp)
        if p and p[0] == typ:
            return sp
    return None


def xfrm(sp):
    x = sp.find(q('p:spPr') + '/' + q('a:xfrm'))
    if x is None:
        return None
    o, e = x.find(q('a:off')), x.find(q('a:ext'))
    return [int(o.get('x')), int(o.get('y')), int(e.get('cx')), int(e.get('cy'))]


def group_map(sp):
    """(sx, sy, ox, oy) mapping child coords -> slide coords for a shape inside nested groups"""
    sx = sy = 1.0; ox = oy = 0.0
    chain = []
    g = sp.getparent()
    while g is not None and g.tag == q('p:grpSp'):
        chain.append(g); g = g.getparent()
    for g in chain:  # innermost first
        x = g.find(q('p:grpSpPr') + '/' + q('a:xfrm'))
        if x is None or x.find(q('a:chExt')) is None:
            continue
        off, ext = x.find(q('a:off')), x.find(q('a:ext'))
        coff, cext = x.find(q('a:chOff')), x.find(q('a:chExt'))
        kx = int(ext.get('cx')) / max(1, int(cext.get('cx'))); ky = int(ext.get('cy')) / max(1, int(cext.get('cy')))
        # compose: new = off + (old - choff) * k
        ox = int(off.get('x')) + (ox - int(coff.get('x'))) * kx; sx *= kx
        oy = int(off.get('y')) + (oy - int(coff.get('y'))) * ky; sy *= ky
    return sx, sy, ox, oy


def real_box(sp):
    b = xfrm(sp)
    if not b:
        return None
    sx, sy, ox, oy = group_map(sp)
    return [int(ox + b[0] * sx), int(oy + b[1] * sy), int(b[2] * sx), int(b[3] * sy)]


def lvl1_attr(sp, attr):
    if sp is None:
        return None
    d = sp.find(q('p:txBody') + '/' + q('a:lstStyle') + '/' + q('a:lvl1pPr') + '/' + q('a:defRPr'))
    return None if d is None else d.get(attr)


def master_title_attr(master, attr):
    d = master.find('.//' + q('p:titleStyle') + '/' + q('a:lvl1pPr') + '/' + q('a:defRPr'))
    return None if d is None else d.get(attr)


def fix_tabs(tree):
    n = 0
    for p in tree.iter(q('a:p')):
        prev = ''
        for t in p.iter(q('a:t')):
            txt = t.text or ''
            new = re.sub(r'(\d)\t+', r'\1 ', txt)
            if new.startswith('\t') and re.search(r'\d$', prev):
                new = ' ' + new.lstrip('\t')
            if new != txt:
                t.text = new; n += 1
            prev = t.text or ''
    return n


HEB = '\u05D0-\u05EA'
PREFIX = set('בהלמשוכ')


def fix_spacing(tree):
    n = 0
    for p in tree.iter(q('a:p')):
        ts = [t for t in p.iter(q('a:t')) if t.text]
        for t in ts:
            new = re.sub('([%s])([A-Za-z])' % HEB, lambda m: m.group(1) + ' ' + m.group(2), t.text)
            new = re.sub('([A-Za-z])([%s])' % HEB, lambda m: m.group(1) + ' ' + m.group(2), new)
            if new != t.text:
                t.text = new; n += 1
        for a, b in zip(ts, ts[1:]):
            x, y = a.text[-1:], b.text[:1]
            heb_x = re.match('[%s]' % HEB, x) is not None; heb_y = re.match('[%s]' % HEB, y) is not None
            lat_x = re.match('[A-Za-z]', x) is not None; lat_y = re.match('[A-Za-z]', y) is not None
            if (heb_x and lat_y) or (lat_x and heb_y):
                # a lone Hebrew prefix letter ("בScrum") gets a hyphen, anything else a space
                word = re.split(r'\s', a.text)[-1]
                if heb_x and len(word) == 1 and word in PREFIX:
                    a.text = a.text + '-'
                else:
                    b.text = ' ' + b.text
                n += 1
    return n


def fix_para_spacing(tree):
    """paragraph spacing given as a % of the line: write it in points so every viewer spaces it the same"""
    n = 0
    for p in tree.iter(q('a:p')):
        ppr = p.find(q('a:pPr'))
        if ppr is None:
            continue
        szs = [int(r.get('sz')) for r in p.iter(q('a:rPr'), q('a:endParaRPr')) if r.get('sz')]
        if not szs:
            continue
        size = max(szs) / 100
        for tag in ('a:spcBef', 'a:spcAft'):
            sp = ppr.find(q(tag))
            pct = sp.find(q('a:spcPct')) if sp is not None else None
            if pct is not None:
                pts = int(round(size * 1.2 * int(pct.get('val')) / 100000 * 100))
                sp.remove(pct)
                etree.SubElement(sp, q('a:spcPts')).set('val', str(pts))
                n += 1
    return n


def fix_rtl_align(tree):
    """Hebrew paragraphs in text boxes with no alignment of their own read right-to-left"""
    n = 0
    for sp in tree.iter(q('p:sp')):
        ph = sp.find('.//' + q('p:ph'))
        if ph is not None and ph.get('type') in ('title', 'ctrTitle', 'subTitle', 'ftr', 'sldNum', 'dt'):
            continue
        body = sp.find(q('p:txBody'))
        if body is None:
            continue
        lvl = body.find(q('a:lstStyle') + '/' + q('a:lvl1pPr'))
        if lvl is not None and lvl.get('algn'):
            continue
        for p in body.findall(q('a:p')):
            txt = ''.join(p.itertext())
            if not re.search('[\u05D0-\u05EA]', txt):
                continue
            ppr = p.find(q('a:pPr'))
            if ppr is None:
                ppr = etree.Element(q('a:pPr')); p.insert(0, ppr)
            if ppr.get('algn') is None and ppr.get('rtl') != '0':
                ppr.set('algn', 'r'); ppr.set('rtl', '1'); n += 1
            elif ppr.get('algn') == 'l' and ppr.get('rtl') != '1' and len(txt) > 30:
                ppr.set('algn', 'r'); ppr.set('rtl', '1'); n += 1
    return n


def fix_parens(tree):
    n = 0
    for p in tree.iter(q('a:p')):
        ts = list(p.iter(q('a:t')))
        s = ''.join(t.text or '' for t in ts)
        new = s
        for pat, rep in PAREN_FIXES:
            new = re.sub(pat, rep, new)
        if new != s and ts:
            # rewrite: keep run boundaries where text is unchanged, put the rest in the run that held the change
            # simplest faithful approach: find common prefix/suffix and edit the run(s) in between
            i = 0
            while i < min(len(s), len(new)) and s[i] == new[i]:
                i += 1
            j = 0
            while j < min(len(s), len(new)) - i and s[-1 - j] == new[-1 - j]:
                j += 1
            mid_new = new[i:len(new) - j]
            # locate runs covering [i, len(s)-j)
            pos = 0; first = None
            for t in ts:
                L = len(t.text or '')
                if first is None and pos + L > i - (1 if i == len(s) - j else 0):
                    first = (t, pos)
                pos += L
            t0, p0 = first
            end = len(s) - j
            # remove changed span from all runs, insert mid_new into first run at offset
            pos = 0
            for t in ts:
                txt = t.text or ''; L = len(txt)
                a, b = max(i, pos), min(end, pos + L)
                if a < b:
                    t.text = txt[:a - pos] + txt[b - pos:]
                pos += L
            off = i - p0
            t0.text = (t0.text or '')[:off] + mid_new + (t0.text or '')[off:]
            n += 1
    return n


def fit_titles(work, W, H):
    pres_rels = rels(os.path.join(work, 'ppt/presentation.xml'))
    pres = load(os.path.join(work, 'ppt/presentation.xml'))
    order = [pres_rels[s.get(q('r:id'))] for s in pres.find(q('p:sldIdLst'))]
    logo_right = int(0.3 * EMU + 0.62 * EMU * 780 / 354 + 0.2 * EMU)
    right_margin = int(0.35 * EMU)
    changed = 0
    report = []
    for si, spath in enumerate(order, 1):
        t = load(spath)
        if t.getroot().get('showMasterSp') == '0':
            continue  # cover / title slides
        lp = [v for v in rels(spath).values() if 'slideLayout' in v][0]
        lay = load(lp)
        if lay.getroot().get('type') == 'title' or lay.getroot().get('showMasterSp') == '0':
            continue  # dark title layout: keep its own title box
        mp = [v for v in rels(lp).values() if 'slideMaster' in v][0]
        mas = load(mp)
        tree_sps = t.find('.//' + q('p:spTree')).findall(q('p:sp'))
        for sp in t.iter(q('p:sp')):
            p = ph_of(sp)
            if not p:
                # a plain text box used as the slide title (top band, one line of large text)
                bx = real_box(sp)
                txt = ''.join(sp.itertext()).strip()
                spPr = sp.find(q('p:spPr'))
                framed = (spPr is not None and (spPr.find(q('a:ln') + '/' + q('a:solidFill')) is not None
                          or spPr.find(q('a:solidFill')) is not None)) or (
                          sp.find(q('p:style')) is not None and (spPr is None or spPr.find(q('a:ln') + '/' + q('a:noFill')) is None))
                sizes_ = [int(r.get('sz')) for r in sp.iter(q('a:rPr')) if r.get('sz')]
                big = (max(sizes_) if sizes_ else 1800) >= 2000
                if bx and bx[1] < 0.95 * EMU and bx[3] < 1.1 * EMU and len(txt) > 8 and big and not framed \
                        and not re.fullmatch(r'[\d.\s|]+', txt):
                    p = ('title', None)
                else:
                    continue
            if p[0] not in ('title', 'ctrTitle'):
                continue
            paras = sp.findall('.//' + q('a:p'))
            texts = [''.join(x.text or '' for x in pp.iter(q('a:t'))).strip() for pp in paras]
            texts = [x for x in texts if x]
            if len(texts) != 1 or sp.find('.//' + q('a:br')) is not None:
                continue  # intentional multi-line titles stay as they are
            lsp = find_ph(lay, p[0]) if ph_of(sp) else None; msp = find_ph(mas, p[0]) if ph_of(sp) else None
            box = real_box(sp) or (xfrm(lsp) if lsp is not None else None) or (xfrm(msp) if msp is not None else None)
            gsx, gsy, gox, goy = group_map(sp)
            if not box:
                continue
            base_sz = lvl1_attr(sp, 'sz') or lvl1_attr(lsp, 'sz') or lvl1_attr(msp, 'sz') or (master_title_attr(mas, 'sz') if ph_of(sp) else '1800') or '4000'
            base_b = lvl1_attr(sp, 'b') or lvl1_attr(lsp, 'b') or (master_title_attr(mas, 'b') if ph_of(sp) else '0') or '0'
            runs = [r for r in sp.iter(q('a:r'))]
            if not runs:
                continue
            width = 0; sizes = []
            for r in runs:
                rp = r.find(q('a:rPr'))
                sz = int((rp.get('sz') if rp is not None and rp.get('sz') else base_sz))
                b = (rp.get('b') if rp is not None and rp.get('b') else base_b) == '1'
                sizes.append(sz)
                width += text_width_in(r.findtext(q('a:t')) or '', sz / 100, b)
            bp = sp.find(q('p:txBody') + '/' + q('a:bodyPr'))
            ins = 0.2
            if bp is not None and bp.get('lIns') is not None:
                ins = (int(bp.get('lIns')) + int(bp.get('rIns', 91440))) / EMU
            avail = box[2] / EMU - ins
            need = width * 1.04
            if need <= avail:
                continue
            # 1) widen to the left, up to the logo, unless another shape is in the way
            x, y, w, h = box
            right = x + w
            new_left = logo_right
            for o in t.iter(q('p:sp'), q('p:pic'), q('p:graphicFrame'), q('p:grpSp'), q('p:cxnSp')):
                if o is sp or o.getparent().tag != q('p:spTree'):
                    continue
                ob = None
                xf = o.find('./*/' + q('a:xfrm')) if o.tag != q('p:graphicFrame') else o.find(q('p:xfrm'))
                if xf is not None and xf.find(q('a:off')) is not None:
                    ob = [int(xf.find(q('a:off')).get('x')), int(xf.find(q('a:off')).get('y')),
                          int(xf.find(q('a:ext')).get('cx')), int(xf.find(q('a:ext')).get('cy'))]
                if not ob or not (ob[1] < y + h and ob[1] + ob[3] > y):
                    continue
                if ob[0] + ob[2] <= x and ob[0] + ob[2] > new_left:
                    new_left = ob[0] + ob[2] + int(0.1 * EMU)
            new_left = min(new_left, x)
            new_right = right
            nw = new_right - new_left
            spPr = sp.find(q('p:spPr'))
            xf = spPr.find(q('a:xfrm'))
            if xf is None:
                xf = etree.SubElement(spPr, q('a:xfrm')); spPr.insert(0, xf)
                etree.SubElement(xf, q('a:off')); etree.SubElement(xf, q('a:ext'))
            xf.find(q('a:off')).set('x', str(int((new_left - gox) / gsx))); xf.find(q('a:off')).set('y', str(int((y - goy) / gsy)))
            xf.find(q('a:ext')).set('cx', str(int(nw / gsx))); xf.find(q('a:ext')).set('cy', str(int(h / gsy)))
            avail = nw / EMU - ins
            scale = 1.0
            if need > avail:
                # 2) shrink the font, but not below 75% or 24pt
                scale = avail / need
                floor = max(0.75, 2400 / max(sizes))
                scale = max(scale, floor)
                for r, sz in zip(runs, sizes):
                    rp = r.find(q('a:rPr'))
                    if rp is None:
                        rp = etree.Element(q('a:rPr')); r.insert(0, rp)
                    rp.set('sz', str(int(round(sz * scale / 50.0)) * 50))
            changed += 1
            report.append((si, texts[0][:50], round(scale, 2), need * scale <= avail + 0.01))
        etree.ElementTree(t.getroot()).write(spath, xml_declaration=True, encoding='UTF-8', standalone=True)
    return changed, report


def main(src, dst):
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    pres = load(os.path.join(work, 'ppt/presentation.xml'))
    sz = pres.find(q('p:sldSz')); W, H = int(sz.get('cx')), int(sz.get('cy'))
    pf = 0
    for f in sorted(os.listdir(os.path.join(work, 'ppt/slides'))):
        if f.endswith('.xml'):
            p = os.path.join(work, 'ppt/slides', f); t = load(p)
            k = fix_parens(t) + fix_tabs(t) + fix_spacing(t)
            fix_para_spacing(t)
            fix_rtl_align(t)
            pf += k
            t.write(p, xml_declaration=True, encoding='UTF-8', standalone=True)
    changed, report = fit_titles(work, W, H)
    out = os.path.abspath(dst)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run(['zip', '-qXrDy', out, '.'], cwd=work, check=True)
    shutil.rmtree(work)
    nofit = [r for r in report if not r[3]]
    print(os.path.basename(src), 'parens fixed:', pf, 'titles adjusted:', changed, 'still 2 lines:', len(nofit))
    for r in nofit:
        print('   ', r)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
