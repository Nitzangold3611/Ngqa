#!/usr/bin/env python3
"""Shrink text in fixed-size shapes (boxes, callouts) whose text runs past the bottom of the shape.
usage: fix_overflow.py in.pptx out.pptx"""
import sys, os, re, zipfile, tempfile, shutil, subprocess
from lxml import etree
from PIL import ImageFont

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
EMU = 914400
FONTS = {b: ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf' % ('Bold' if b else 'Regular'), 100)
         for b in (0, 1)}


def q(t):
    p, n = t.split(':'); return '{%s}%s' % ({'a': A, 'p': P}[p], n)


def wlen(s, pt, b):
    return FONTS[b].getlength(s) / 100 * pt / 72


def para_runs(p, scale, base):
    """list of (text, size_pt, bold) for a paragraph"""
    out = []
    if callable(base):
        base = base(p)
    for r in p:
        if r.tag == q('a:r'):
            rp = r.find(q('a:rPr'))
            sz = int(rp.get('sz')) / 100 if rp is not None and rp.get('sz') else base
            b = 1 if rp is not None and rp.get('b') == '1' else 0
            out.append((r.findtext(q('a:t')) or '', sz * scale, b))
        elif r.tag == q('a:br'):
            out.append(('\n', base * scale, 0))
    return out


def needed_height(body, width_in, scale, base):
    total = 0.0
    for p in body.findall(q('a:p')):
        runs = para_runs(p, scale, base)
        ppr = p.find(q('a:pPr'))
        indent = int(ppr.get('marL', 0)) / EMU if ppr is not None else 0
        lnpct = 1.0
        if ppr is not None and ppr.find(q('a:lnSpc') + '/' + q('a:spcPct')) is not None:
            lnpct = int(ppr.find(q('a:lnSpc') + '/' + q('a:spcPct')).get('val')) / 100000
        maxsz = max([s for _, s, _ in runs] or [(base(p) if callable(base) else base) * scale])
        if not ''.join(t for t, _, _ in runs).strip():
            total += maxsz * 1.2 * lnpct / 72
            continue
        # greedy wrap over words, keeping each run's size
        lines, x = 1, 0.0
        avail = max(0.2, width_in - indent)
        for text, sz, b in runs:
            if text == '\n':
                lines += 1; x = 0; continue
            for i, word in enumerate(re.split(r'(\s+)', text)):
                if not word:
                    continue
                w = wlen(word, sz, b)
                if word.isspace():
                    x += w; continue
                if x + w > avail and x > 0:
                    lines += 1; x = 0
                    while w > avail:  # a single word longer than the line
                        lines += 1; w -= avail
                x += w
        sp_after = 0
        for tag in ('a:spcAft', 'a:spcBef'):
            if ppr is not None and ppr.find(q(tag) + '/' + q('a:spcPts')) is not None:
                sp_after += int(ppr.find(q(tag) + '/' + q('a:spcPts')).get('val')) / 100 / 72
            elif ppr is not None and ppr.find(q(tag) + '/' + q('a:spcPct')) is not None:
                sp_after += maxsz * 1.2 * int(ppr.find(q(tag) + '/' + q('a:spcPct')).get('val')) / 100000 / 72
        total += lines * maxsz * 1.2 * lnpct / 72 + sp_after
    return total


def apply_scale(body, base, scale):
    for p in body.findall(q('a:p')):
        pb = base(p) if callable(base) else base
        for r in list(p.findall(q('a:r'))) + list(p.findall(q('a:endParaRPr'))):
            rp = r.find(q('a:rPr')) if r.tag == q('a:r') else r
            if rp is None:
                rp = etree.Element(q('a:rPr')); r.insert(0, rp)
            sz = int(rp.get('sz')) / 100 if rp.get('sz') else pb
            rp.set('sz', str(max(900, int(sz * scale * 2) * 50)))


def layout_lines(body, width_in, scale, base):
    out = []; y = 0.0
    for p in body.findall(q('a:p')):
        runs = para_runs(p, scale, base)
        ppr = p.find(q('a:pPr'))
        rtl = ppr is not None and ppr.get('rtl') == '1'
        heb = re.search('[\u0590-\u05FF]', ''.join(t for t, _, _ in runs)) is not None
        algn = (ppr.get('algn') if ppr is not None else None) or ('r' if (rtl or heb) else 'l')
        indent = int(ppr.get('marL', 0)) / EMU if ppr is not None else 0
        lnpct = 1.0
        if ppr is not None and ppr.find(q('a:lnSpc') + '/' + q('a:spcPct')) is not None:
            lnpct = int(ppr.find(q('a:lnSpc') + '/' + q('a:spcPct')).get('val')) / 100000
        maxsz = max([sz for _, sz, _ in runs] or [(base(p) if callable(base) else base) * scale])
        lh = maxsz * 1.2 * lnpct / 72
        avail = max(0.2, width_in - indent)
        widths = [0.0]
        for text, sz, b in runs:
            if text == '\n':
                widths.append(0.0); continue
            for word in re.split(r'(\s+)', text):
                if not word:
                    continue
                w = wlen(word, sz, b)
                if word.isspace():
                    widths[-1] += w; continue
                if widths[-1] + w > avail and widths[-1] > 0:
                    widths.append(0.0)
                widths[-1] += w
        for tag in ('a:spcBef',):
            if ppr is not None and ppr.find(q(tag) + '/' + q('a:spcPts')) is not None:
                y += int(ppr.find(q(tag) + '/' + q('a:spcPts')).get('val')) / 100 / 72
        for w in widths:
            out.append((y, y + lh, min(w, avail) + indent, algn))
            y += lh
        if ppr is not None and ppr.find(q('a:spcAft') + '/' + q('a:spcPts')) is not None:
            y += int(ppr.find(q('a:spcAft') + '/' + q('a:spcPts')).get('val')) / 100 / 72
    return out


def fix_shape(sp, sx=1.0, sy=1.0, siblings=()):
    body = sp.find(q('p:txBody'))
    if body is None:
        return False
    ph = sp.find('.//' + q('p:ph'))
    if ph is not None:
        # placeholders only when the slide states both their box and every text size
        if ph.get('type') in ('title', 'ctrTitle', 'subTitle', 'ftr', 'sldNum', 'dt'):
            return False
        if sp.find(q('p:spPr') + '/' + q('a:xfrm')) is None:
            key = (ph.get('type', 'body'), ph.get('idx'))
            lx = LAYOUT_PH.get(key)
            if lx is None:
                lx = LAYOUT_PH.get((key[0], None))
            if lx is None:
                return False
            spPr = sp.find(q('p:spPr'))
            if spPr is None:
                return False
            spPr.insert(0, etree.fromstring(etree.tostring(lx)))
        pass
    if not ''.join(body.itertext()).strip():
        return False
    bp = body.find(q('a:bodyPr'))
    if bp is not None and (bp.get('wrap') == 'none'
                           or bp.get('vert') not in (None, 'horz')):
        return False
    xf = sp.find(q('p:spPr') + '/' + q('a:xfrm'))
    if xf is None or xf.find(q('a:ext')) is None:
        return False
    if xf.get('rot') not in (None, '0'):
        return False
    w = int(xf.find(q('a:ext')).get('cx')) * sx / EMU
    h = int(xf.find(q('a:ext')).get('cy')) * sy / EMU
    lI = int(bp.get('lIns', 91440)) / EMU if bp is not None else 0.1
    rI = int(bp.get('rIns', 91440)) / EMU if bp is not None else 0.1
    tI = int(bp.get('tIns', 45720)) / EMU if bp is not None else 0.05
    bI = int(bp.get('bIns', 45720)) / EMU if bp is not None else 0.05
    ls = body.find(q('a:lstStyle') + '/' + q('a:lvl1pPr') + '/' + q('a:defRPr'))
    base = int(ls.get('sz')) / 100 if ls is not None and ls.get('sz') else (BODY_BASE if ph is not None else 18.0)
    if ph is not None and not (ls is not None and ls.get('sz')):
        def base(p, _b=base):
            ppr = p.find(q('a:pPr'))
            lvl = int(ppr.get('lvl', 0)) if ppr is not None else 0
            return BODY_LVL.get(lvl, _b)
    na = bp.find(q('a:normAutofit')) if bp is not None else None
    if na is not None and na.get('fontScale'):
        fsc = int(na.get('fontScale')) / 100000
        if callable(base):
            base = (lambda f, k: (lambda p: f(p) * k))(base, fsc)
        else:
            base *= fsc
    width, height = (w - lI - rI) * 0.97, h - tI - bI
    # a short label (a number like "5.1") must never break: keep it on one line
    paras_ = [p for p in body.findall(q('a:p')) if ''.join(p.itertext()).strip()]
    label = ''.join(body.itertext()).strip()
    if bp is not None and ph is None and len(paras_) == 1 and len(label) <= 24 and body.find('.//' + q('a:br')) is None:
        runs_ = [r for r in body.iter(q('a:r'))]
        szs = [int(r.find(q('a:rPr')).get('sz')) / 100 for r in runs_ if r.find(q('a:rPr')) is not None and r.find(q('a:rPr')).get('sz')]
        bld = any(r.find(q('a:rPr')) is not None and r.find(q('a:rPr')).get('b') == '1' for r in runs_)
        if wlen(label, max(szs or [18.0]), 1 if bld else 0) > width:
            bp.set('wrap', 'none')
            return True
    if width < 0.3 or height < 0.2:
        return False
    need = needed_height(body, width, 1.0, base)
    # text that would run into another shape directly below counts as overflow too
    x0 = int(xf.find(q('a:off')).get('x')); y0 = int(xf.find(q('a:off')).get('y'))
    w0 = int(xf.find(q('a:ext')).get('cx')); h0 = int(xf.find(q('a:ext')).get('cy'))
    anchor_top = (bp is None or bp.get('anchor') in (None, 't'))
    blockers = []
    if anchor_top and sx == 1.0 and sy == 1.0:
        for o in siblings:
            if o is sp or o.tag not in (q('p:sp'), q('p:pic'), q('p:graphicFrame'), q('p:grpSp')):
                continue
            if o.tag == q('p:sp') and not ''.join(o.itertext()).strip():
                continue
            nm = o.find('./*/' + q('p:cNvPr'))
            if nm is not None and (nm.get('name') or '').startswith('Icon '):
                continue  # our own icons move out of the way instead
            ox = o.find('./*/' + q('a:xfrm')) if o.tag != q('p:graphicFrame') else o.find(q('p:xfrm'))
            if ox is None or ox.find(q('a:off')) is None:
                continue
            a, b = int(ox.find(q('a:off')).get('x')), int(ox.find(q('a:off')).get('y'))
            c = int(ox.find(q('a:ext')).get('cx'))
            ov = min(a + c, x0 + w0) - max(a, x0)
            if o.tag == q('p:sp') and c < 3 * EMU:
                continue  # small labels placed on purpose next to the text
            if ov > 0 and y0 + 0.3 * EMU < b < y0 + h0:
                blockers.append((a / EMU, (a + c) / EMU, b / EMU))

    if sx == 1.0 and sy == 1.0 and y0 < SLIDE_H - 0.9 * EMU:
        blockers.append((0.0, SLIDE_W / EMU, (SLIDE_H - 0.46 * EMU) / EMU))  # copyright line

    def collides(scale):
        if not blockers:
            return False
        left_edge = x0 / EMU + lI; right_edge = (x0 + w0) / EMU - rI
        for ytop, ybot, lw, al in layout_lines(body, width, scale, base):
            yb = y0 / EMU + tI + ybot
            if al == 'r':
                xs, xe = right_edge - lw, right_edge
            elif al == 'ctr':
                mid = (left_edge + right_edge) / 2; xs, xe = mid - lw / 2, mid + lw / 2
            else:
                xs, xe = left_edge, left_edge + lw
            for a, c, b in blockers:
                if yb > b + 0.02 and xs < c and xe > a and lw > 0.05:
                    return True
        return False
    overflow = need > height * 1.03
    coll = collides(1.0)
    if ph is not None:
        overflow = False  # PowerPoint fits placeholder text itself; only fix text running under other shapes
    if not overflow and not coll:
        return False
    if coll and not overflow:
        # text running under a picture/box: shrink a little, or leave it alone
        lo2, hi2 = 0.6, 1.0
        if collides(0.6):
            return False
        for _ in range(10):
            mid = (lo2 + hi2) / 2
            if collides(mid):
                hi2 = mid
            else:
                lo2 = mid
        apply_scale(body, base, lo2)
        return True
    autofit = bp is not None and bp.find(q('a:spAutoFit')) is not None
    floor = 0.55
    if autofit:
        # the box grows in PowerPoint; only act if growing would run into something below it
        x0 = int(xf.find(q('a:off')).get('x')); y0 = int(xf.find(q('a:off')).get('y'))
        w0 = int(xf.find(q('a:ext')).get('cx')); h0 = int(xf.find(q('a:ext')).get('cy'))
        grown = y0 + int((need + tI + bI) * EMU)
        hit = False
        for o in siblings:
            if o is sp:
                continue
            ox = o.find('./*/' + q('a:xfrm')) if o.tag != q('p:graphicFrame') else o.find(q('p:xfrm'))
            if ox is None or ox.find(q('a:off')) is None:
                continue
            a, b = int(ox.find(q('a:off')).get('x')), int(ox.find(q('a:off')).get('y'))
            c, d = int(ox.find(q('a:ext')).get('cx')), int(ox.find(q('a:ext')).get('cy'))
            if a < x0 + w0 and a + c > x0 and y0 + h0 - 20000 <= b < grown:
                hit = True; break
        if not hit and not collides(1.0):
            return False
        floor = 0.7
    lo, hi = 0.5, 1.0
    for _ in range(14):
        mid = (lo + hi) / 2
        if needed_height(body, width, mid, base) <= height and not collides(mid):
            lo = mid
        else:
            hi = mid
    scale = max(lo, floor)
    apply_scale(body, base, scale)
    return True


BODY_BASE = 24.0
SLIDE_W = 12192000
SLIDE_H = 6858000
BODY_LVL = {}
LAYOUT_PH = {}
NO_HEBREW = {'Calibri', 'Calibri Light', 'Segoe UI Semilight', 'Franklin Gothic Medium Cond', 'Franklin Gothic Medium'}


def hebrew_font(tree):
    # fonts without Hebrew letters make PowerPoint and browsers pick an unpredictable fallback: use Arial
    for cs in tree.iter(q('a:cs')):
        if cs.get('typeface') in NO_HEBREW:
            cs.set('typeface', 'Arial')
            for k in ('panose', 'pitchFamily', 'charset'):
                cs.attrib.pop(k, None)


def walk(tree):
    hebrew_font(tree)
    n = 0
    tr = tree.find('.//' + q('p:spTree'))

    def rec(parent, sx, sy):
        nonlocal n
        for ch in parent:
            if ch.tag == q('p:sp'):
                if fix_shape(ch, sx, sy, list(parent)):
                    n += 1
            elif ch.tag == q('p:grpSp'):
                gx = ch.find(q('p:grpSpPr') + '/' + q('a:xfrm'))
                ksx, ksy = sx, sy
                if gx is not None and gx.find(q('a:chExt')) is not None:
                    cx, cy = int(gx.find(q('a:ext')).get('cx')), int(gx.find(q('a:ext')).get('cy'))
                    chx, chy = int(gx.find(q('a:chExt')).get('cx')), int(gx.find(q('a:chExt')).get('cy'))
                    if chx and chy:
                        ksx, ksy = sx * cx / chx, sy * cy / chy
                rec(ch, ksx, ksy)
    rec(tr, 1.0, 1.0)
    return n


def main(src, dst):
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    global BODY_BASE, SLIDE_W, SLIDE_H
    pz = etree.parse(os.path.join(work, 'ppt/presentation.xml')).find(q('p:sldSz'))
    SLIDE_W, SLIDE_H = int(pz.get('cx')), int(pz.get('cy'))
    mf = os.path.join(work, 'ppt/slideMasters/slideMaster1.xml')
    if os.path.exists(mf):
        m = etree.parse(mf).find('.//' + q('p:bodyStyle') + '/' + q('a:lvl1pPr') + '/' + q('a:defRPr'))
        if m is not None and m.get('sz'):
            BODY_BASE = int(m.get('sz')) / 100
        bs = etree.parse(mf).find('.//' + q('p:bodyStyle'))
        for i in range(9):
            d = bs.find(q('a:lvl%dpPr' % (i + 1)) + '/' + q('a:defRPr')) if bs is not None else None
            if d is not None and d.get('sz'):
                BODY_LVL[i] = int(d.get('sz')) / 100
    sd = os.path.join(work, 'ppt/slides')
    tot = 0; where = []
    for f in sorted(os.listdir(sd), key=lambda s: int(re.sub(r'\D', '', s) or 0)):
        if not f.endswith('.xml'):
            continue
        p = os.path.join(sd, f)
        t = etree.parse(p)
        LAYOUT_PH.clear()
        rp = os.path.join(sd, '_rels', f + '.rels')
        if os.path.exists(rp):
            lt = re.search(r'Target="../slideLayouts/(slideLayout\d+\.xml)"', open(rp, encoding='utf-8').read())
            if lt:
                lay = etree.parse(os.path.join(work, 'ppt/slideLayouts', lt.group(1)))
                for lsp in lay.iter(q('p:sp')):
                    lph = lsp.find('.//' + q('p:ph')); lxf = lsp.find(q('p:spPr') + '/' + q('a:xfrm'))
                    if lph is not None and lxf is not None:
                        LAYOUT_PH[(lph.get('type', 'body'), lph.get('idx'))] = lxf
                        LAYOUT_PH.setdefault((lph.get('type', 'body'), None), lxf)
        k = walk(t)
        if k:
            tot += k; where.append(f.replace('.xml', '').replace('slide', ''))
        t.write(p, xml_declaration=True, encoding='UTF-8', standalone=True)
    out = os.path.abspath(dst)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run(['zip', '-qXrDy', out, '.'], cwd=work, check=True)
    shutil.rmtree(work)
    print(os.path.basename(src), 'shapes shrunk:', tot, 'slide files:', ','.join(where))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
