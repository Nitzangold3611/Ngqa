#!/usr/bin/env python3
"""Shrink SmartArt text so no single word is broken across lines.
usage: fix_smartart.py in.pptx out.pptx"""
import sys, os, re, zipfile, tempfile, shutil, subprocess
from lxml import etree
from PIL import ImageFont

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
DSP = 'http://schemas.microsoft.com/office/drawing/2008/diagram'
DGM = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'
EMU = 914400
F = {b: ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf' % ('Bold' if b else 'Regular'), 100) for b in (0, 1)}


def wlen(s, pt, b):
    return F[b].getlength(s) / 100 * pt / 72  # inches


def main(src, dst):
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    ddir = os.path.join(work, 'ppt/diagrams')
    total = 0
    if os.path.isdir(ddir):
        for f in sorted(os.listdir(ddir)):
            if not f.startswith('drawing') or not f.endswith('.xml'):
                continue
            path = os.path.join(ddir, f)
            t = etree.parse(path)
            changed_words = {}
            touched = []
            for sp in t.iter('{%s}sp' % DSP):
                body = sp.find('{%s}txBody' % DSP)
                xf = sp.find('{%s}txXfrm' % DSP)
                if xf is None:
                    xf = sp.find('{%s}spPr/{%s}xfrm' % (DSP, A))
                if body is None or xf is None:
                    continue
                w = int(xf.find('{%s}ext' % A).get('cx'))
                if xf.tag == '{%s}xfrm' % A and xf.get('rot') in ('5400000', '16200000'):
                    w = int(xf.find('{%s}ext' % A).get('cy'))
                geom = sp.find('{%s}spPr/{%s}prstGeom' % (DSP, A))
                shrink = 1.0
                if geom is not None and geom.get('prst') in ('chevron', 'homePlate', 'pentagon'):
                    # LibreOffice wraps inside the arrow's narrow text area: keep labels on one line
                    bp0 = body.find('{%s}bodyPr' % A)
                    if bp0 is not None and len((''.join(body.itertext())).split()) <= 2:
                        bp0.set('wrap', 'none'); shrink = 0.92; touched.append(f)
                bp = body.find('{%s}bodyPr' % A)
                ins = (int(bp.get('lIns', 91440)) + int(bp.get('rIns', 91440))) / EMU if bp is not None else 0.2
                avail = w / EMU * shrink - ins - 0.05
                runs = list(body.iter('{%s}r' % A))
                if not runs:
                    continue
                worst = 1.0
                for r in runs:
                    rp = r.find('{%s}rPr' % A)
                    sz = int(rp.get('sz', '1800')) if rp is not None else 1800
                    b = 1 if rp is not None and rp.get('b') == '1' else 0
                    for word in (r.findtext('{%s}t' % A) or '').split():
                        need = wlen(word, sz / 100, b)
                        if need > avail:
                            worst = min(worst, avail / need)
                if worst < 1.0:
                    for r in runs:
                        rp = r.find('{%s}rPr' % A)
                        sz = int(rp.get('sz', '1800'))
                        new = max(1000, int(sz * worst / 100) * 100)
                        rp.set('sz', str(new))
                        changed_words[(r.findtext('{%s}t' % A) or '').strip()] = new
                    total += 1
            # keep sibling shapes of the same kind at one size
            if changed_words:
                for prst in ('chevron', 'homePlate', 'pentagon'):
                    sps = [sp for sp in t.iter('{%s}sp' % DSP)
                           if sp.find('{%s}spPr/{%s}prstGeom' % (DSP, A)) is not None
                           and sp.find('{%s}spPr/{%s}prstGeom' % (DSP, A)).get('prst') == prst
                           and list(sp.iter('{%s}r' % A))]
                    sizes = [int(r.find('{%s}rPr' % A).get('sz', '1800')) for sp in sps for r in sp.iter('{%s}r' % A)]
                    if sizes and min(sizes) != max(sizes):
                        m = min(sizes)
                        for sp in sps:
                            for r in sp.iter('{%s}r' % A):
                                r.find('{%s}rPr' % A).set('sz', str(m))
                                changed_words[(r.findtext('{%s}t' % A) or '').strip()] = m
            if touched and not changed_words:
                t.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)
                print('  ', f, 'labels kept on one line')
            if changed_words:
                t.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)
                # mirror the sizes in the matching data part, so PowerPoint keeps them when it redraws
                dpath = os.path.join(ddir, f.replace('drawing', 'data'))
                if os.path.exists(dpath):
                    d = etree.parse(dpath)
                    for r in d.iter('{%s}r' % A):
                        txt = (r.findtext('{%s}t' % A) or '').strip()
                        if txt in changed_words:
                            rp = r.find('{%s}rPr' % A)
                            if rp is None:
                                rp = etree.Element('{%s}rPr' % A); r.insert(0, rp)
                            rp.set('sz', str(changed_words[txt]))
                    d.write(dpath, xml_declaration=True, encoding='UTF-8', standalone=True)
                print('  ', f, changed_words)
    out = os.path.abspath(dst)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run(['zip', '-qXrDy', out, '.'], cwd=work, check=True)
    shutil.rmtree(work)
    print(os.path.basename(src), 'smartart shapes resized:', total)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
