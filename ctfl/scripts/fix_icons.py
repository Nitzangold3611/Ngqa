#!/usr/bin/env python3
"""Move (or drop) icons, and move/shrink pictures, that sit on top of text, using a render of the deck without them.
usage: fix_icons.py in.pptx out.pptx"""
import sys, os, re, zipfile, tempfile, shutil, subprocess, glob
from lxml import etree
from PIL import Image, ImageFont
FONT = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', 100)

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
EMU = 914400
SOFFICE = '/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx/scripts/office/soffice.py'
DPI = 40


def q(t):
    p, n = t.split(':'); return '{%s}%s' % ({'a': A, 'p': P}[p], n)


def order(work):
    rels = open(os.path.join(work, 'ppt/_rels/presentation.xml.rels'), encoding='utf-8').read()
    m = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1)
         for r in re.findall(r'<Relationship [^>]*>', rels)}
    pres = open(os.path.join(work, 'ppt/presentation.xml'), encoding='utf-8').read()
    return [os.path.join(work, 'ppt', m[r]) for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)]


def icons(t):
    out = []
    for pic in t.find('.//' + q('p:spTree')).findall(q('p:pic')):
        nm = pic.find('.//' + q('p:cNvPr'))
        if nm is not None and (nm.get('name') or '').startswith('Icon '):
            out.append(pic)
    return out


def box(el):
    xf = el.find('./*/' + q('a:xfrm')) if el.tag != q('p:graphicFrame') else el.find(q('p:xfrm'))
    if xf is None or xf.find(q('a:off')) is None or xf.find(q('a:ext')) is None:
        return None
    return [int(xf.find(q('a:off')).get('x')), int(xf.find(q('a:off')).get('y')),
            int(xf.find(q('a:ext')).get('cx')), int(xf.find(q('a:ext')).get('cy'))]


def is_logo(el):
    nm = el.find('.//' + q('p:cNvPr'))
    return nm is not None and (nm.get('name') or '').startswith('NGQA')


def dark_ratio(img, box):
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return 1.0
    reg = img.crop((x0, y0, x1, y1)).convert('L')
    h = reg.histogram()
    return sum(h[:235]) / max(1, (x1 - x0) * (y1 - y0))


def main(src, dst):
    work = tempfile.mkdtemp(); probe = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(work); z.extractall(probe)
    pres = etree.parse(os.path.join(work, 'ppt/presentation.xml'))
    sz = pres.find(q('p:sldSz')); W, H = int(sz.get('cx')), int(sz.get('cy'))
    # 1) a copy without the icons, rendered
    for sp in order(probe):
        t = etree.parse(sp)
        tr = t.find('.//' + q('p:spTree'))
        for el in list(tr):
            if el.tag in (q('p:pic'), q('p:graphicFrame'), q('p:grpSp')) and not is_logo(el):
                tr.remove(el)
            elif el.tag == q('p:sp') and el.find('.//' + q('p:ph')) is None:
                b = box(el)
                if b and b[2] < 3 * EMU:
                    tr.remove(el)
        t.write(sp, xml_declaration=True, encoding='UTF-8', standalone=True)
    rdir = tempfile.mkdtemp()
    subprocess.run(['zip', '-qXrDy', os.path.join(rdir, 'p.pptx'), '.'], cwd=probe, check=True)
    subprocess.run(['python3', SOFFICE, '--headless', '--convert-to', 'pdf', 'p.pptx'], cwd=rdir,
                   capture_output=True, timeout=900)
    subprocess.run(['pdftoppm', '-png', '-r', str(DPI), 'p.pdf', 's'], cwd=rdir, check=True)
    pages = sorted(glob.glob(os.path.join(rdir, 's-*.png')))
    px = DPI / EMU
    moved = dropped = 0
    moved_pics = []
    for i, sp in enumerate(order(work)):
        t = etree.parse(sp)
        ics = icons(t)
        if not ics:
            continue
        img = Image.open(pages[i]).convert('RGB')
        taken = []
        for pic in ics:
            xf = pic.find(q('p:spPr') + '/' + q('a:xfrm'))
            off, ext = xf.find(q('a:off')), xf.find(q('a:ext'))
            x, y, s = int(off.get('x')), int(off.get('y')), int(ext.get('cx'))
            pad = 0.06 * EMU
            ibx = ((x - pad) * px, (y - pad) * px, (x + s + pad) * px, (y + s + pad) * px)
            if dark_ratio(img, ibx) < 0.004 and not any(abs(x - a) < s and abs(y - b) < s for a, b in taken):
                taken.append((x, y)); continue
            # search free spots, nearest first
            best = None
            for side in (s, int(s * 0.8)):
                step = int(0.1 * EMU)
                for yy in range(int(1.3 * EMU), int(H - side - 0.55 * EMU), step):
                    for xx in range(int(0.25 * EMU), int(W - side - 0.25 * EMU), step):
                        if any(abs(xx - a) < side and abs(yy - b) < side for a, b in taken):
                            continue
                        bb = ((xx - pad) * px, (yy - pad) * px, (xx + side + pad) * px, (yy + side + pad) * px)
                        if dark_ratio(img, bb) < 0.002:
                            d = (xx - x) ** 2 + (yy - y) ** 2
                            if best is None or d < best[0]:
                                best = (d, xx, yy, side)
                if best:
                    break
            if best:
                _, xx, yy, side = best
                off.set('x', str(xx)); off.set('y', str(yy)); ext.set('cx', str(side)); ext.set('cy', str(side))
                taken.append((xx, yy)); moved += 1
            else:
                pic.getparent().remove(pic); dropped += 1
        t.write(sp, xml_declaration=True, encoding='UTF-8', standalone=True)
    # pictures that cover the main text: move to free space nearby, or shrink
    for i, sp in enumerate(order(work)):
        t = etree.parse(sp)
        tr = t.find('.//' + q('p:spTree'))
        pics = [p for p in tr.findall(q('p:pic')) if not is_logo(p) and p not in icons(t)]
        if not pics:
            continue
        img = Image.open(pages[i]).convert('RGB')
        labels = [box(e) for e in tr.findall(q('p:sp')) if e.find('.//' + q('p:ph')) is None
                  and box(e) and box(e)[2] < 3 * EMU and ''.join(e.itertext()).strip()]
        others = [box(e) for e in tr if e.tag in (q('p:pic'), q('p:graphicFrame'), q('p:grpSp')) and box(e)]
        changed = False
        for pic in pics:
            b = box(pic)
            if not b or b[2] * b[3] > 0.35 * W * H:
                continue
            x, y, w, h = b
            pb = (x * px, y * px, (x + w) * px, (y + h) * px)
            if dark_ratio(img, pb) < 0.004:
                continue
            if any(l[0] < x + w and l[0] + l[2] > x and l[1] < y + h and l[1] + l[3] > y for l in labels):
                continue  # captions/labels belong to this picture: leave it
            best = None
            for k in (1.0, 0.85, 0.7, 0.6):
                ww, hh = int(w * k), int(h * k)
                step = int(0.1 * EMU)
                for yy in range(int(1.0 * EMU), int(H - hh - 0.5 * EMU), step):
                    for xx in range(int(0.2 * EMU), int(W - ww - 0.2 * EMU), step):
                        if any(o != b and o[0] < xx + ww and o[0] + o[2] > xx and o[1] < yy + hh and o[1] + o[3] > yy for o in others):
                            continue
                        m = 0.12 * EMU
                        bb = ((xx - m) * px, (yy - m) * px, (xx + ww + m) * px, (yy + hh + m) * px)
                        if dark_ratio(img, bb) < 0.0008:
                            d = (xx - x) ** 2 + (yy - y) ** 2
                            if best is None or d < best[0]:
                                best = (d, xx, yy, ww, hh)
                if best:
                    break
            if best:
                _, xx, yy, ww, hh = best
                xf = pic.find(q('p:spPr') + '/' + q('a:xfrm'))
                xf.find(q('a:off')).set('x', str(xx)); xf.find(q('a:off')).set('y', str(yy))
                xf.find(q('a:ext')).set('cx', str(ww)); xf.find(q('a:ext')).set('cy', str(hh))
                others = [o for o in others if o != b] + [[xx, yy, ww, hh]]
                moved_pics.append(i + 1); changed = True
        if changed:
            t.write(sp, xml_declaration=True, encoding='UTF-8', standalone=True)
    print('   pictures moved on slides:', moved_pics)
    # small text boxes (formulas, notes) lying on the main text: slide them sideways into free space
    moved_lbl = []
    for i, sp in enumerate([] if True else order(work)):
        t = etree.parse(sp)
        tr = t.find('.//' + q('p:spTree'))
        img = Image.open(pages[i]).convert('RGB')
        changed = False
        for el in tr.findall(q('p:sp')):
            if el.find('.//' + q('p:ph')) is not None or not ''.join(el.itertext()).strip():
                continue
            b = box(el)
            if not b or b[2] >= 3 * EMU or b[1] < 1.0 * EMU:
                continue
            x, y, w, h = b
            # does its text area cover main text?  (shrink to the middle 70% to ignore anti-aliasing)
            cb = ((x + w * .15) * px, (y + h * .2) * px, (x + w * .85) * px, (y + h * .8) * px)
            if dark_ratio(img, cb) < 0.003:
                continue
            best = None
            step = int(0.05 * EMU)
            # use the width the text really needs, not the box
            szs = [int(r.get('sz')) for r in el.iter(q('a:rPr')) if r.get('sz')]
            longest = max((''.join(p.itertext()) for p in el.iter(q('a:p'))), key=len)
            need = FONT.getlength(longest) / 100 * (max(szs or [1800]) / 100) / 72 * EMU + 0.15 * EMU
            ox = x
            if need < w:
                algn = (el.find('.//' + q('a:pPr')).get('algn') if el.find('.//' + q('a:pPr')) is not None else None)
                ox = x + (w - need) if algn == 'r' else (x + (w - need) / 2 if algn == 'ctr' else x)
                w = int(need)
            for xx in range(int(0.2 * EMU), int(W - w - 0.2 * EMU), step):
                bb = (xx * px, y * px, (xx + w) * px, (y + h) * px)
                if dark_ratio(img, bb) < 0.002:
                    d = abs(xx - ox)
                    if best is None or d < best[0]:
                        best = (d, xx)
            if best and best[0] < 4 * EMU:
                el.find(q('p:spPr') + '/' + q('a:xfrm') + '/' + q('a:off')).set('x', str(int(best[1] - (ox - x))))
                changed = True; moved_lbl.append(i + 1)
        if changed:
            t.write(sp, xml_declaration=True, encoding='UTF-8', standalone=True)
    print('   text boxes moved on slides:', moved_lbl)
    out = os.path.abspath(dst)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run(['zip', '-qXrDy', out, '.'], cwd=work, check=True)
    for d in (work, probe, rdir):
        shutil.rmtree(d)
    print(os.path.basename(src), 'icons moved:', moved, 'dropped:', dropped)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
