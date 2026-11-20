#!/usr/bin/env python3
"""Insert a linked table-of-contents slide after the cover, and a "back to contents" link on every slide.
usage: add_toc.py deck_number in.pptx out.pptx"""
import sys, os, re, zipfile, tempfile, shutil, subprocess, json
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'toc_def.py')).read())

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
RELNS = 'http://schemas.openxmlformats.org/package/2006/relationships'
SLIDE_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide'
EMU = 914400
NAVY, TEAL_D, ORANGE, TINT = '121133', '0E9F97', 'F38911', 'E8F9F8'
SKILL = '/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx/scripts'
CHAPTER = {1: 'מבוא לבדיקות תוכנה', 2: 'בדיקות לאורך מחזור חיי התוכנה', 3: 'בדיקות סטטיות',
           4: 'טכניקות בדיקה', 5: 'ניהול בדיקות', 6: 'כלי בדיקה'}


def q(t):
    p, n = t.split(':'); return '{%s}%s' % ({'a': A, 'p': P, 'r': R}[p], n)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def rels_path(part):
    d, f = os.path.split(part)
    return os.path.join(d, '_rels', f + '.rels')


def add_rel(part, target):
    rp = rels_path(part)
    t = etree.parse(rp)
    ids = {r.get('Id') for r in t.getroot()}
    n = 1
    while 'rIdL%d' % n in ids:
        n += 1
    el = etree.SubElement(t.getroot(), '{%s}Relationship' % RELNS)
    el.set('Id', 'rIdL%d' % n); el.set('Type', SLIDE_REL); el.set('Target', target)
    t.write(rp, xml_declaration=True, encoding='UTF-8', standalone=True)
    return 'rIdL%d' % n


def order(work):
    rels = open(os.path.join(work, 'ppt/_rels/presentation.xml.rels'), encoding='utf-8').read()
    m = {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1)
         for r in re.findall(r'<Relationship [^>]*>', rels)}
    pres = open(os.path.join(work, 'ppt/presentation.xml'), encoding='utf-8').read()
    return [m[r] for r in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres)]


def entry_xml(sid, rid, x, y, w, h, label, level, sz):
    """one clickable line: the whole box is the link, so the text keeps its own colour"""
    if level == 1:
        fill = f'<a:solidFill><a:srgbClr val="{TINT}"/></a:solidFill>'
        geom = '<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 22000"/></a:avLst></a:prstGeom>'
        m = re.match(r'^(\d+(?:\.\d+)*)\s+(.*)$', label)
        num, rest = (m.group(1), m.group(2)) if m else ('', label)
        runs = ''
        if num:
            runs += (f'<a:r><a:rPr lang="he-IL" sz="{sz}" b="1"><a:solidFill><a:srgbClr val="{ORANGE}"/></a:solidFill>'
                     f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{esc(num)}  </a:t></a:r>')
        runs += (f'<a:r><a:rPr lang="he-IL" sz="{sz}" b="1"><a:solidFill><a:srgbClr val="{NAVY}"/></a:solidFill>'
                 f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{esc(rest)}</a:t></a:r>')
        ins = 'lIns="91440" rIns="137160"'
        marR = 0
    else:
        fill = '<a:noFill/>'
        geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        runs = (f'<a:r><a:rPr lang="he-IL" sz="{sz}"><a:solidFill><a:srgbClr val="{TEAL_D}"/></a:solidFill>'
                f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>›  </a:t></a:r>'
                f'<a:r><a:rPr lang="he-IL" sz="{sz}"><a:solidFill><a:srgbClr val="2B2A4C"/></a:solidFill>'
                f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{esc(label)}</a:t></a:r>')
        ins = 'lIns="91440" rIns="91440"'
        marR = 320040
    return etree.fromstring(
        f'<p:sp xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:nvSpPr><p:cNvPr id="{sid}" name="TOC {esc(label)[:40]}">'
        f'<a:hlinkClick r:id="{rid}" action="ppaction://hlinksldjump"/></p:cNvPr><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>{geom}{fill}<a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="none" {ins} tIns="0" bIns="0" anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle/>'
        f'<a:p><a:pPr algn="r" rtl="1" marR="{marR}"/>{runs}</a:p></p:txBody></p:sp>')


def main(n, src, dst):
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    pres = etree.parse(os.path.join(work, 'ppt/presentation.xml'))
    sz = pres.find(q('p:sldSz')); W, H = int(sz.get('cx')), int(sz.get('cy'))
    wide = W / H > 1.5
    before = order(work)
    # a content slide's layout gives the light background, logo and copyright line
    lay_of = {}
    for s in before[2:12]:
        rel = open(rels_path(os.path.join(work, 'ppt', s)), encoding='utf-8').read()
        L = re.search(r'slideLayouts/(slideLayout\d+\.xml)', rel).group(1)
        lay_of[L] = lay_of.get(L, 0) + 1
    layout = max(lay_of, key=lay_of.get)
    out = subprocess.run(['python3', os.path.join(SKILL, 'add_slide.py'), work, layout,
                          '--after', os.path.basename(before[0])], capture_output=True, text=True, cwd=SKILL)
    if out.returncode:
        raise SystemExit(out.stderr)
    after = order(work)
    toc_part = os.path.join(work, 'ppt', after[1])
    assert after[1] not in before
    # targets: entry slide k in the final deck before insertion is index k (1-based) -> shifted by one now
    entries = TOC[n]
    t = etree.parse(toc_part)
    tr = t.find('.//' + q('p:spTree'))
    for el in list(tr):
        if el.tag not in (q('p:nvGrpSpPr'), q('p:grpSpPr')):
            tr.remove(el)
    sid = 10
    # title
    title = f'תוכן עניינים · פרק {n}: {CHAPTER[n]}'
    tx = 2.2 * EMU if wide else 1.6 * EMU
    tr.append(etree.fromstring(
        f'<p:sp xmlns:p="{P}" xmlns:a="{A}"><p:nvSpPr><p:cNvPr id="{sid}" name="TOC Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{int(tx)}" y="{int(0.28 * EMU)}"/><a:ext cx="{int(W - tx - 0.45 * EMU)}" cy="{int(0.7 * EMU)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square" lIns="0" rIns="0" anchor="ctr"><a:normAutofit/></a:bodyPr><a:lstStyle/>'
        f'<a:p><a:pPr algn="r" rtl="1"/><a:r><a:rPr lang="he-IL" sz="{3000 if wide else 2600}" b="1"><a:solidFill><a:srgbClr val="{NAVY}"/></a:solidFill>'
        f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{esc(title)}</a:t></a:r></a:p>'
        f'<a:p><a:pPr algn="r" rtl="1"/><a:r><a:rPr lang="he-IL" sz="1200"><a:solidFill><a:srgbClr val="7C7B98"/></a:solidFill>'
        f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>לחיצה על נושא עוברת לשקף הראשון שלו</a:t></a:r></a:p></p:txBody></p:sp>'))
    sid += 1
    # layout of entries: one or two columns, right column first (RTL)
    top, bottom = 1.35 * EMU, H - 0.62 * EMU
    cols = 1 if len(entries) <= 11 else 2
    if cols == 2:
        # break between sections, as evenly as possible
        starts = [i for i, e in enumerate(entries) if e[0] == 1 and i > 0]
        half = min(starts, key=lambda i: max(i, len(entries) - i)) if starts else (len(entries) + 1) // 2
        groups = [entries[:half], entries[half:]]
    else:
        groups = [entries]
    rows = max(len(g) for g in groups)
    rh = min(0.42 * EMU, (bottom - top) / rows)
    fs = int(max(1050, min(1600, rh / EMU * 72 * 0.52 * 100)) / 50) * 50
    margin = 0.5 * EMU
    gap = 0.35 * EMU
    cw = (W - 2 * margin - gap * (cols - 1)) / cols if cols == 2 else min(8.5 * EMU, W - 2 * margin)
    links = []
    for ci, g in enumerate(groups):
        right = W - margin - ci * (cw + gap) if cols == 2 else (W + cw) / 2
        for ri, (level, label, slide_no) in enumerate(g):
            target = after[slide_no]  # slide_no counted before the insert -> index shifts by one
            rid = add_rel(toc_part, os.path.basename(target))
            y = top + ri * rh + rh * 0.08
            hh = rh * 0.84
            w = cw if level == 1 else cw - 0.3 * EMU
            x = right - w
            tr.append(entry_xml(sid, rid, x, y, w, hh, label, level, fs if level == 2 else fs + 100))
            sid += 1
            links.append({'slide': slide_no + 1, 'x': round(x / W * 100, 2), 'y': round(y / H * 100, 2),
                          'w': round(w / W * 100, 2), 'h': round(hh / H * 100, 2)})
    t.write(toc_part, xml_declaration=True, encoding='UTF-8', standalone=True)
    # "back to contents" on every slide: one linked button on the slide master(s)
    toc_name = os.path.basename(toc_part)
    for mf in sorted(os.listdir(os.path.join(work, 'ppt/slideMasters'))):
        if not mf.endswith('.xml'):
            continue
        mp = os.path.join(work, 'ppt/slideMasters', mf)
        mt = etree.parse(mp)
        rid = add_rel(mp, '../slides/' + toc_name)
        mtr = mt.find('.//' + q('p:spTree'))
        ids = [int(x) for x in mt.xpath('//p:cNvPr/@id', namespaces={'p': P}) if x.isdigit()]
        bw, bh = (1.55 if wide else 1.15) * EMU, (0.3 if wide else 0.26) * EMU
        bx, by = W - bw - (0.3 if wide else 0.15) * EMU, H - (0.4 if wide else 0.36) * EMU
        mtr.append(etree.fromstring(
            f'<p:sp xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:nvSpPr><p:cNvPr id="{max(ids) + 1}" name="Back to contents">'
            f'<a:hlinkClick r:id="{rid}" action="ppaction://hlinksldjump"/></p:cNvPr><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(bx)}" y="{int(by)}"/><a:ext cx="{int(bw)}" cy="{int(bh)}"/></a:xfrm>'
            f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 50000"/></a:avLst></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{NAVY}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="none" lIns="45720" rIns="45720" tIns="0" bIns="0" anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle/>'
            f'<a:p><a:pPr algn="ctr" rtl="1"/><a:r><a:rPr lang="he-IL" sz="900" b="1"><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
            f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>☰ תוכן עניינים</a:t></a:r></a:p></p:txBody></p:sp>'))
        mt.write(mp, xml_declaration=True, encoding='UTF-8', standalone=True)
    o = os.path.abspath(dst)
    if os.path.exists(o):
        os.remove(o)
    subprocess.run(['zip', '-qXrDy', o, '.'], cwd=work, check=True)
    shutil.rmtree(work)
    json.dump({'toc_slide': 2, 'links': links,
               'back': {'x': round(bx / W * 100, 2), 'y': round(by / H * 100, 2), 'w': round(bw / W * 100, 2), 'h': round(bh / H * 100, 2)}},
              open(f'/home/claude/work/toc_links_{n}.json', 'w'))
    print(f'deck {n}: contents slide added with {len(entries)} links')


if __name__ == '__main__':
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3])
