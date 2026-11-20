#!/usr/bin/env python3
"""Restyle an existing deck into the NGQA design, keeping every text run as is.
usage: restyle.py in.pptx out.pptx"""
import sys, os, re, zipfile, shutil, hashlib, tempfile, glob, subprocess
from lxml import etree

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
RELNS = 'http://schemas.openxmlformats.org/package/2006/relationships'
IMG_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
NS = {'a': A, 'p': P, 'r': R}
EMU = 914400
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

NAVY, TEAL, TEAL_D, ORANGE, BODY, GRAY = '121133', '14DACD', '0E9F97', 'F38911', '23224A', '7C7B98'

ICON_RULES = [  # (keywords, icon)  checked in order against slide text
    (['שאלה', 'שאלות', 'מבחן'], 'FaQuestion'),
    (['כותב', 'מחבר', 'Author', 'רשם', 'Scribe'], 'FaPen'),
    (['מנהל', 'Manager', 'הנהלה'], 'FaUserTie'),
    (['מנחה', 'Moderator', 'facilitator', 'מוביל'], 'FaChalkboardTeacher'),
    (['סוקר', 'Reviewer'], 'FaEye'),
    (['Checklist', "צ'קליסט"], 'FaClipboardCheck'),
    (['הצלחה', 'success', 'גורמים'], 'FaTrophy'),
    (['מסמך', 'מסמכי', 'דרישות', 'תיעוד'], 'FaFileAlt'),
    (['קוד', 'Code', 'code'], 'FaCode'),
    (['פגם', 'תקלה', 'תקלות', 'באג', 'bug', 'Bug', 'defect'], 'FaBug'),
    (['סיכון', 'סיכונים', 'Risk'], 'FaExclamationTriangle'),
    (['תכנון', 'תכנית', 'Planning', 'plan'], 'FaTasks'),
    (['סקירה', 'סקירות', 'Review', 'review'], 'FaComments'),
    (['תפקיד', 'צוות', 'משתתפ', 'team'], 'FaUsers'),
    (['כלי', 'Tool', 'tool'], 'FaTools'),
    (['אוטומצי', 'Automation'], 'FaRobot'),
    (['תהליך', 'Process', 'process'], 'FaProjectDiagram'),
    (['ניתוח', 'מדד', 'Metric', 'דוח'], 'FaChartBar'),
    (['תיקון', 'Fix'], 'FaWrench'),
    (['זמן', 'לוח'], 'FaClock'),
    (['עלות', 'תקציב', 'Cost'], 'FaMoneyBillWave'),
    (['לקוח', 'קבלה', 'Acceptance'], 'FaHandshake'),
    (['רגרסיה', 'Regression', 'חוזר'], 'FaRedo'),
    (['רמות', 'Level', 'level'], 'FaLayerGroup'),
    (['ניהול', 'Management', 'בקרה'], 'FaCogs'),
    (['בדיק', 'Test', 'test'], 'FaCheckCircle'),
]
FALLBACK = ['FaSearch', 'FaLightbulb', 'FaBook', 'FaLaptopCode']
CLIP_HINTS = ('Local Settings', 'Temporary Internet', 'CAGCAT', 'AppData', 'MEDIA\\', 'Clip', 'clip', 'j0', 'MC9')


def q(tag):
    pre, t = tag.split(':')
    return '{%s}%s' % (NS[pre], t)


def load(path):
    return etree.parse(path, etree.XMLParser(remove_blank_text=False))


def save(tree, path):
    tree.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)


def rels_path(part):
    d, f = os.path.split(part)
    return os.path.join(d, '_rels', f + '.rels')


class Pkg:
    def __init__(self, root):
        self.root = root
        self.media_cache = {}
        os.makedirs(os.path.join(root, 'ppt/media'), exist_ok=True)

    def media(self, asset):
        if asset not in self.media_cache:
            name = 'ngqa_' + os.path.basename(asset)
            shutil.copy(asset, os.path.join(self.root, 'ppt/media', name))
            self.media_cache[asset] = name
        return self.media_cache[asset]

    def add_image_rel(self, part, asset):
        rp = rels_path(part)
        t = load(rp)
        ids = {r.get('Id') for r in t.getroot()}
        n = 1
        while 'rIdN%d' % n in ids:
            n += 1
        rid = 'rIdN%d' % n
        el = etree.SubElement(t.getroot(), '{%s}Relationship' % RELNS)
        el.set('Id', rid); el.set('Type', IMG_REL); el.set('Target', '../media/' + self.media(asset))
        save(t, rp)
        return rid

    def rel_targets(self, part):
        rp = rels_path(part)
        if not os.path.exists(rp):
            return {}
        return {r.get('Id'): r.get('Target') for r in load(rp).getroot()}


def pic_xml(rid, x, y, w, h, sid, name, descr=''):
    return etree.fromstring(
        f'<p:pic xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:nvPicPr><p:cNvPr id="{sid}" name="{name}" descr="{descr}"/>'
        f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
        f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
        f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


def bg_xml(rid):
    return etree.fromstring(
        f'<p:bg xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:bgPr><a:blipFill dpi="0" rotWithShape="1">'
        f'<a:blip r:embed="{rid}"/><a:srcRect/><a:stretch><a:fillRect/></a:stretch></a:blipFill>'
        f'<a:effectLst/></p:bgPr></p:bg>')


def solid(color):
    return etree.fromstring(f'<a:solidFill xmlns:a="{A}"><a:srgbClr val="{color}"/></a:solidFill>')


def set_fill(rpr, color):
    for f in rpr.findall(q('a:solidFill')) + rpr.findall(q('a:gradFill')) + rpr.findall(q('a:noFill')):
        rpr.remove(f)
    # solidFill must come after ln and before effects/latin etc.
    idx = 0
    for i, ch in enumerate(rpr):
        if ch.tag == q('a:ln'):
            idx = i + 1
    rpr.insert(idx, solid(color))


def max_id(tree):
    ids = [int(x) for x in tree.xpath('//p:cNvPr/@id', namespaces=NS) if x.isdigit()]
    return max(ids or [1])


def ph_type(sp):
    ph = sp.find('.//' + q('p:nvPr') + '/' + q('p:ph'))
    if ph is None:
        return None
    return ph.get('type', 'body')


def strip_decor(tree):
    """remove every non-placeholder element from the spTree"""
    tr = tree.find('.//' + q('p:spTree'))
    for ch in list(tr):
        if ch.tag in (q('p:nvGrpSpPr'), q('p:grpSpPr')):
            continue
        if ch.tag == q('p:sp') and ph_type(ch):
            continue
        tr.remove(ch)
    return tr


def insert_after_header(tr, el):
    # right after grpSpPr so it sits behind placeholders
    i = [c.tag for c in tr].index(q('p:grpSpPr'))
    tr.insert(i + 1, el)


FOOTER = 'כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה. חל איסור להשתמש או לשכפל את החומרים בשל זכויות יוצרים'


def footer_box(W, H, sid, color):
    x = int((2.3 if W / H > 1.5 else 1.45) * EMU); w = W - 2 * x
    return etree.fromstring(
        f'<p:sp xmlns:p="{P}" xmlns:a="{A}"><p:nvSpPr><p:cNvPr id="{sid}" name="NGQA Footer"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{int(H - 0.42 * EMU)}"/><a:ext cx="{w}" cy="{int(0.3 * EMU)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"></a:bodyPr><a:lstStyle/>'
        f'<a:p><a:pPr algn="ctr" rtl="1"/><a:r><a:rPr lang="he-IL" sz="{1000 if W / H > 1.5 else 900}" dirty="0"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{FOOTER}</a:t></a:r></a:p></p:txBody></p:sp>')


def style_footer_sp(sp):
    for rpr in sp.iter(q('a:rPr'), q('a:defRPr'), q('a:endParaRPr')):
        rpr.set('i', '0')
        rpr.set('sz', '900')
        set_fill(rpr, GRAY)
        for tag in ('a:latin', 'a:cs'):
            for f in rpr.findall(q(tag)):
                f.set('typeface', 'Arial')


def set_lvl_color(style_el, color, bold=None, bu=None):
    if style_el is None:
        return
    for lvl in style_el:
        if not lvl.tag.endswith('pPr'):
            continue
        d = lvl.find(q('a:defRPr'))
        if d is None:
            d = etree.SubElement(lvl, q('a:defRPr'))
        set_fill(d, color)
        if bold is not None:
            d.set('b', '1' if bold else '0')
        for tag in ('a:latin', 'a:cs'):
            f = d.find(q(tag))
            if f is not None and not f.get('typeface', '').startswith('+'):
                f.set('typeface', 'Arial')
        if bu:
            old = lvl.find(q('a:buClr'))
            if old is not None:
                lvl.remove(old)
            bc = etree.fromstring(f'<a:buClr xmlns:a="{A}"><a:srgbClr val="{bu(lvl)}"/></a:buClr>')
            # buClr goes before buSzX/buFont/buChar...
            pos = len(lvl)
            for i, ch in enumerate(lvl):
                if ch.tag.split('}')[1] in ('buClrTx', 'buSzTx', 'buSzPct', 'buSzPts', 'buFontTx', 'buFont',
                                            'buNone', 'buAutoNum', 'buChar', 'buBlip', 'tabLst', 'defRPr', 'extLst'):
                    pos = i
                    break
            lvl.insert(pos, bc)


def theme(path):
    t = load(path)
    cs = t.find('.//' + q('a:clrScheme'))
    cs.set('name', 'NGQA')
    vals = {'dk1': '000000', 'lt1': 'FFFFFF', 'dk2': NAVY, 'lt2': 'E8F9F8', 'accent1': TEAL_D, 'accent2': ORANGE,
            'accent3': NAVY, 'accent4': TEAL, 'accent5': '4A47A3', 'accent6': 'D9534F', 'hlink': TEAL_D,
            'folHlink': '4A47A3'}
    for k, v in vals.items():
        el = cs.find(q('a:' + k))
        for c in list(el):
            el.remove(c)
        etree.SubElement(el, q('a:srgbClr')).set('val', v)
    for fnt in t.iter(q('a:majorFont'), q('a:minorFont')):
        fnt.find(q('a:latin')).set('typeface', 'Arial')
        cs_ = fnt.find(q('a:cs'))
        if cs_ is not None:
            cs_.set('typeface', 'Arial')
        for f in fnt.findall(q('a:font')):
            if f.get('script') == 'Hebr':
                f.set('typeface', 'Arial')
    save(t, path)


def is_grayish(fill):
    c = fill.find(q('a:srgbClr'))
    if c is None:
        s = fill.find(q('a:schemeClr'))
        return s is not None and s.get('val') in ('tx1', 'dk1', 'tx2', 'dk2', 'bg1', 'lt1')
    v = c.get('val')
    r, g, b = int(v[:2], 16), int(v[2:4], 16), int(v[4:], 16)
    return max(r, g, b) - min(r, g, b) < 40


def slide_text(tree):
    return ' '.join(tree.xpath('//a:t/text()', namespaces=NS))


def pick_icon(text, used, title=''):
    for src in (title, text):
        for kws, icon in ICON_RULES:
            if icon in used or (icon == 'FaQuestion' and src is text):
                continue
            if any(k in src for k in kws):
                return icon
    for icon in FALLBACK:
        if icon not in used:
            return icon
    return 'FaSearch'


def make_cover(t, spath, pkg, W, H, bg_dark, full):
    root = t.getroot()
    root.set('showMasterSp', '0')
    cs = t.find(q('p:cSld'))
    cs.insert(0, bg_xml(pkg.add_image_rel(spath, bg_dark)))
    tr = t.find('.//' + q('p:spTree'))
    lh = H * 0.62; lw = lh * 700 / 821
    insert_after_header(tr, pic_xml(pkg.add_image_rel(spath, full), W * 0.06, (H - lh) / 2, lw, lh,
                                    max_id(t) + 1, 'NGQA Logo', 'NGQA logo'))
    tx0 = W * 0.06 + lw + W * 0.04
    texts = [sp for sp in tr.findall(q('p:sp')) if ''.join(sp.xpath('.//a:t/text()', namespaces=NS)).strip()]
    for k, sp in enumerate(texts):
        sppr = sp.find(q('p:spPr'))
        x = sppr.find(q('a:xfrm'))
        if x is not None:
            sppr.remove(x)
        y, h = (H * 0.30, H * 0.24) if k == 0 else (H * 0.56, H * 0.14)
        sppr.insert(0, etree.fromstring(
            f'<a:xfrm xmlns:a="{A}"><a:off x="{int(tx0)}" y="{int(y)}"/><a:ext cx="{int(W - tx0 - W * 0.06)}" cy="{int(h)}"/></a:xfrm>'))
        bp = sp.find(q('p:txBody') + '/' + q('a:bodyPr'))
        if bp is not None:
            bp.set('anchor', 'b' if k == 0 else 't'); bp.set('wrap', 'square')
            for a_ in list(bp):
                if a_.tag in (q('a:spAutoFit'), q('a:normAutofit')):
                    bp.remove(a_)
        for p_ in sp.iter(q('a:p')):
            ppr = p_.find(q('a:pPr'))
            if ppr is None:
                ppr = etree.Element(q('a:pPr')); p_.insert(0, ppr)
            ppr.set('algn', 'r'); ppr.set('rtl', '1')
        for rpr in sp.iter(q('a:rPr'), q('a:endParaRPr')):
            set_fill(rpr, 'FFFFFF' if k == 0 else TEAL)
            rpr.set('sz', '4800' if k == 0 else '2200'); rpr.set('b', '1')
    tr.append(footer_box(W, H, max_id(t) + 1, '9FA0C8'))


def is_cover(t, idx):
    tr = t.find('.//' + q('p:spTree'))
    if tr.findall(q('p:pic')) or tr.findall(q('p:graphicFrame')) or tr.findall(q('p:grpSp')):
        return False
    txt = ''.join(t.xpath('//a:t/text()', namespaces=NS)).strip()
    return 0 < len(txt) <= 22 and (idx == 0 or re.match(r'^ISTQB', txt) is not None)


def restyle(src, dst):
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    pkg = Pkg(work)
    pres = load(os.path.join(work, 'ppt/presentation.xml'))
    sz = pres.find(q('p:sldSz'))
    W, H = int(sz.get('cx')), int(sz.get('cy'))
    wide = W / H > 1.5
    ct = load(os.path.join(work, '[Content_Types].xml'))
    if not any(d.get('Extension', '').lower() == 'png' for d in ct.getroot()):
        e = etree.SubElement(ct.getroot(), '{http://schemas.openxmlformats.org/package/2006/content-types}Default')
        e.set('Extension', 'png'); e.set('ContentType', 'image/png')
        save(ct, os.path.join(work, '[Content_Types].xml'))

    bg_light = os.path.join(ASSETS, 'bg_light.png' if wide else 'bg_light43.png')
    bg_dark = os.path.join(ASSETS, 'bg_dark.png' if wide else 'bg_dark43.png')
    badge = os.path.join(ASSETS, 'logo_badge.png')
    full = os.path.join(ASSETS, 'logo_full_t.png')

    for th in glob.glob(os.path.join(work, 'ppt/theme/theme*.xml')):
        theme(th)

    title_layouts = set()
    # ---------- masters
    for mp in glob.glob(os.path.join(work, 'ppt/slideMasters/slideMaster*.xml')):
        t = load(mp)
        cs = t.find(q('p:cSld'))
        old = cs.find(q('p:bg'))
        if old is not None:
            cs.remove(old)
        cs.insert(0, bg_xml(pkg.add_image_rel(mp, bg_light)))
        tr = strip_decor(t)
        bh = int((0.62 if wide else 0.48) * EMU); bw = int(bh * 780 / 354)
        insert_after_header(tr, pic_xml(pkg.add_image_rel(mp, badge), int(0.3 * EMU), int((0.25 if wide else 0.14) * EMU), bw, bh,
                                        max_id(t) + 1, 'NGQA Logo', 'NGQA logo'))
        for sp in tr.findall(q('p:sp')):
            if ph_type(sp) in ('ftr', 'sldNum', 'dt'):
                style_footer_sp(sp)
        tr.append(footer_box(W, H, max_id(t) + 1, GRAY))
        tx = t.find('.//' + q('p:txStyles'))
        set_lvl_color(tx.find(q('p:titleStyle')), NAVY, bold=True)
        set_lvl_color(tx.find(q('p:bodyStyle')), BODY,
                      bu=lambda lvl: ORANGE if lvl.tag.endswith('lvl1pPr') else TEAL_D)
        save(t, mp)

    # ---------- layouts
    for lp in glob.glob(os.path.join(work, 'ppt/slideLayouts/slideLayout*.xml')):
        t = load(lp)
        root = t.getroot()
        cs = t.find(q('p:cSld'))
        old = cs.find(q('p:bg'))
        if old is not None:
            cs.remove(old)
        tr = strip_decor(t)
        for sp in tr.findall(q('p:sp')):
            if ph_type(sp) in ('ftr', 'sldNum', 'dt'):
                style_footer_sp(sp)
        if root.get('type') == 'title':
            title_layouts.add(os.path.basename(lp))
            cs.insert(0, bg_xml(pkg.add_image_rel(lp, bg_dark)))
            root.set('showMasterSp', '0')
            lh = H * 0.62; lw = lh * 700 / 821
            insert_after_header(tr, pic_xml(pkg.add_image_rel(lp, full), W * 0.06, (H - lh) / 2, lw, lh,
                                            max_id(t) + 1, 'NGQA Logo', 'NGQA logo'))
            tr.append(footer_box(W, H, max_id(t) + 1, '9FA0C8'))
            tx0 = W * 0.06 + lw + W * 0.04
            for sp in tr.findall(q('p:sp')):
                pt = ph_type(sp)
                if pt in ('ctrTitle', 'title', 'subTitle'):
                    sppr = sp.find(q('p:spPr'))
                    x = sppr.find(q('a:xfrm'))
                    if x is not None:
                        sppr.remove(x)
                    y, h = (H * 0.28, H * 0.26) if pt != 'subTitle' else (H * 0.56, H * 0.14)
                    sppr.insert(0, etree.fromstring(
                        f'<a:xfrm xmlns:a="{A}"><a:off x="{int(tx0)}" y="{int(y)}"/><a:ext cx="{int(W - tx0 - W * 0.06)}" cy="{int(h)}"/></a:xfrm>'))
                    body = sp.find(q('p:txBody'))
                    bp = body.find(q('a:bodyPr'))
                    bp.set('anchor', 'b' if pt != 'subTitle' else 't')
                    ls = body.find(q('a:lstStyle'))
                    if ls is None:
                        ls = etree.Element(q('a:lstStyle')); body.insert(1, ls)
                    lvl = ls.find(q('a:lvl1pPr'))
                    if lvl is None:
                        lvl = etree.SubElement(ls, q('a:lvl1pPr'))
                    lvl.set('algn', 'r'); lvl.set('rtl', '1')
                    set_lvl_color(ls, 'FFFFFF' if pt != 'subTitle' else TEAL, bold=(pt != 'subTitle'))
                    d = lvl.find(q('a:defRPr')); d.set('sz', '4400' if pt != 'subTitle' else '2000')
                elif pt in ('ftr', 'sldNum', 'dt'):
                    for rpr in sp.iter(q('a:rPr'), q('a:defRPr'), q('a:endParaRPr')):
                        set_fill(rpr, '9FA0C8')
        else:
            if root.get('showMasterSp') == '0':
                del root.attrib['showMasterSp']
            for sp in tr.findall(q('p:sp')):
                if ph_type(sp) == 'title':
                    body = sp.find(q('p:txBody'))
                    if body is None:
                        continue
                    ls = body.find(q('a:lstStyle'))
                    if ls is None:
                        ls = etree.Element(q('a:lstStyle')); body.insert(1, ls)
                    if ls.find(q('a:lvl1pPr')) is None:
                        ls.insert(0, etree.Element(q('a:lvl1pPr')))
                    set_lvl_color(ls, NAVY, bold=True)
        save(t, lp)

    # ---------- slides
    logo_hashes = set()
    stats = {'logos': 0, 'icons': 0, 'removed': 0}
    pres_rels = pkg.rel_targets(os.path.join(work, 'ppt/presentation.xml'))
    order = [pres_rels[s.get(q('r:id'))] for s in pres.find(q('p:sldIdLst'))]
    for sidx, target in enumerate(order):
        spath = os.path.join(work, 'ppt', target)
        t = load(spath)
        rel = pkg.rel_targets(spath)
        layout = os.path.basename([v for v in rel.values() if 'slideLayout' in v][0])
        is_title = layout in title_layouts
        t.getroot().attrib.pop('showMasterSp', None)
        cs = t.find(q('p:cSld'))
        old = cs.find(q('p:bg'))
        if old is not None:
            cs.remove(old)
        text = slide_text(t)
        title = ' '.join(x for sp in t.iter(q('p:sp')) if ph_type(sp) in ('title', 'ctrTitle')
                         for x in sp.xpath('.//a:t/text()', namespaces=NS))
        used = set()
        tr = t.find('.//' + q('p:spTree'))
        for pic in list(tr.findall(q('p:pic'))):
            blip = pic.find('.//' + q('a:blip'))
            xf = pic.find(q('p:spPr') + '/' + q('a:xfrm'))
            off = xf.find(q('a:off')) if xf is not None else None
            ext = xf.find(q('a:ext')) if xf is not None else None
            if pic.getparent() is not tr:
                continue
            if blip is None or off is None or ext is None:
                continue
            tgt = rel.get(blip.get(q('r:embed')), '')
            mpath = os.path.normpath(os.path.join(os.path.dirname(spath), tgt))
            try:
                h = hashlib.md5(open(mpath, 'rb').read()).hexdigest()
            except OSError:
                h = ''
            x, y, w, hh = int(off.get('x')), int(off.get('y')), int(ext.get('cx')), int(ext.get('cy'))
            descr = pic.find('.//' + q('p:cNvPr')).get('descr', '') or ''
            parent = pic.getparent()
            # old logo: small picture hugging the top-left corner
            if (x < 0.5 * EMU and y < 0.35 * EMU and w < 2.6 * EMU and hh < 1.4 * EMU) or h in logo_hashes:
                logo_hashes.add(h)
                parent.remove(pic); stats['logos'] += 1
                continue
            if is_title:
                parent.remove(pic); stats['removed'] += 1
                continue
            ext_ = os.path.splitext(tgt)[1].lower()
            small = w < 3.6 * EMU and hh < 3.6 * EMU
            clip = small and (ext_ in ('.wmf', '.emf', '.gif') or any(k in descr for k in CLIP_HINTS))
            if clip:
                icon = pick_icon(text, used, title); used.add(icon)
                side = max(min(min(w, hh), int(1.35 * EMU)), int(0.95 * EMU))
                cx, cy = x + w / 2, y + hh / 2
                nx = min(max(cx - side / 2, 0.25 * EMU), W - side - 0.25 * EMU)
                ny = min(max(cy - side / 2, 1.3 * EMU), H - side - 0.55 * EMU)
                new = pic_xml(pkg.add_image_rel(spath, os.path.join(ASSETS, 'icons', icon + '.png')),
                              nx, ny, side, side, max_id(t) + 1, 'Icon ' + icon, icon[2:] + ' icon')
                new.find('.//' + q('p:nvPr')).attrib.pop('userDrawn', None)
                parent.replace(pic, new); stats['icons'] += 1
        for sp in tr.iter(q('p:sp')):
            pt = ph_type(sp)
            if pt in ('ftr', 'sldNum', 'dt'):
                if is_title:
                    for rpr in sp.iter(q('a:rPr'), q('a:endParaRPr')):
                        set_fill(rpr, '9FA0C8'); rpr.set('i', '0')
                else:
                    style_footer_sp(sp)
            elif pt in ('title', 'ctrTitle', 'subTitle') or (is_title and pt == 'body'):
                if is_title:
                    sppr = sp.find(q('p:spPr'))
                    x = sppr.find(q('a:xfrm'))
                    if x is not None:
                        sppr.remove(x)
                    for rpr in sp.iter(q('a:rPr'), q('a:endParaRPr')):
                        for f in rpr.findall(q('a:solidFill')):
                            rpr.remove(f)
                else:
                    rprs = list(sp.iter(q('a:rPr'), q('a:endParaRPr')))
                    vals = {etree.tostring(f) for r_ in rprs for f in r_.findall(q('a:solidFill'))}
                    for rpr in rprs:
                        f = rpr.find(q('a:solidFill'))
                        if f is not None and (is_grayish(f) or len(vals) == 1):
                            set_fill(rpr, NAVY)
        if not is_title and is_cover(t, sidx):
            make_cover(t, spath, pkg, W, H, bg_dark, full)
            stats['covers'] = stats.get('covers', 0) + 1
        save(t, spath)

    out = os.path.abspath(dst)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run(['zip', '-qXrDy', out, '.'], cwd=work, check=True)
    shutil.rmtree(work)
    print(os.path.basename(src), stats)


if __name__ == '__main__':
    restyle(sys.argv[1], sys.argv[2])
