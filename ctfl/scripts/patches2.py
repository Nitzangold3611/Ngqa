#!/usr/bin/env python3
"""Fixes from user feedback 20.11.2026 (applied on final_N.pptx). usage: patches2.py N in.pptx out.pptx"""
import sys, copy
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from lxml import etree
N = int(sys.argv[1]); P = Presentation(sys.argv[2])
NAVY = RGBColor(0x12, 0x11, 0x33); TEAL = RGBColor(0x0E, 0x9F, 0x97); ORANGE = RGBColor(0xF3, 0x89, 0x11); BODY = RGBColor(0x2B, 0x2A, 0x4C)
WHITE = RGBColor(255, 255, 255)

def walk(shs):
    for s in shs:
        yield s
        if s.shape_type == 6: yield from walk(s.shapes)

def text_box(sl, x, y, w, h, txt, pt=16, color=BODY, bold=False, align=PP_ALIGN.CENTER, name='Text'):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tb.name = name
    tf = tb.text_frame; tf.word_wrap = True
    for a in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'): setattr(tf, a, 0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = align; r = p.add_run(); r.text = txt
    r.font.size = Pt(pt); r.font.bold = bold; r.font.color.rgb = color; r.font.name = 'Arial'
    return tb

def set_size(sh, pt, wrap=True, ins0=False):
    tf = sh.text_frame; tf.word_wrap = wrap
    if ins0: tf.margin_top = tf.margin_bottom = 0; tf.margin_left = tf.margin_right = Inches(0.03)
    for p in tf.paragraphs:
        for r in p.runs: r.font.size = Pt(pt)
        epr = p._p.find(qn('a:endParaRPr'))
        if epr is not None: epr.set('sz', str(int(pt * 100)))

def node(sl, x, y, w, h, txt, fill, line, color, pt, bold=False, geom=MSO_SHAPE.ROUNDED_RECTANGLE, name='Node'):
    s = sl.shapes.add_shape(geom, Inches(x), Inches(y), Inches(w), Inches(h)); s.name = name
    s.fill.solid(); s.fill.fore_color.rgb = fill
    s.line.color.rgb = line; s.line.width = Pt(1.25); s.shadow.inherit = False
    tf = s.text_frame; tf.word_wrap = True
    for a in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'): setattr(tf, a, Inches(0.02))
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = txt
    r.font.size = Pt(pt); r.font.bold = bold; r.font.color.rgb = color; r.font.name = 'Arial'
    return s

def arrow(sl, x1, y1, x2, y2, color, head=True):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)); c.name = 'Link'
    c.line.color.rgb = color; c.line.width = Pt(1.5)
    if head:
        ln = c.line._get_or_add_ln(); t = etree.SubElement(ln, qn('a:tailEnd')); t.set('type', 'triangle'); t.set('w', 'med'); t.set('len', 'med')
    return c

def send_back(sl, shapes):
    tree = sl.shapes._spTree
    for s in shapes:
        el = s._element; tree.remove(el); tree.insert(2, el)

if N == 4:
    # --- slide 25: number line labels 1 and 5 under the ticks
    sl = P.slides[24]
    body = [s for s in sl.shapes if s.shape_id == 2][0]
    p = body.text_frame.paragraphs[7]
    assert p.text.strip().replace('\t', '') in ('5 1', '51')
    for r in p.runs: r.text = ''
    text_box(sl, 4.56, 3.9, 0.5, 0.35, '1', 18, NAVY, True, name='Tick label 1')
    text_box(sl, 7.56, 3.9, 0.5, 0.35, '5', 18, NAVY, True, name='Tick label 5')

    # --- slide 33: decision table as a real table
    sl = P.slides[32]
    old = [s for s in sl.shapes if s.name in ('Rectangle 2', 'Line 3')]
    assert len(old) == 2
    for s in old: s._element.getparent().remove(s._element)
    tm = sl._element.find(qn('p:timing'))
    if tm is not None: sl._element.remove(tm)
    rows = [('', [str(i) for i in range(1, 9)]),
            ('C1', '1 1 1 1 0 0 0 0'.split()), ('C2', '1 1 0 0 1 1 0 0'.split()), ('C3', '1 0 1 0 1 0 1 0'.split()),
            ('A1', [''] * 8), ('A2', [''] * 8)]
    x0, y0, cw0, cw, rh = 1.15, 1.85, 0.75, 0.62, 0.52
    gt = sl.shapes.add_table(len(rows), 9, Inches(x0), Inches(y0), Inches(cw0 + 8 * cw), Inches(rh * len(rows)))
    gt.name = 'Decision Table'; tbl = gt.table
    tblPr = tbl._tbl.tblPr
    for a in ('firstRow', 'bandRow'): tblPr.set(a, '0')
    sid = tblPr.find(qn('a:tableStyleId'))
    if sid is not None: sid.text = '{5940675A-B579-460E-94D1-54222C63F5DA}'  # No Style, Table Grid
    tbl.columns[0].width = Inches(cw0)
    for j in range(1, 9): tbl.columns[j].width = Inches(cw)
    for i, (lab, vals) in enumerate(rows):
        tbl.rows[i].height = Inches(rh)
        cond = 1 <= i <= 3; act = i >= 4
        for j, txt in enumerate([lab] + vals):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.02); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            if i == 0: c.fill.fore_color.rgb = NAVY
            elif j == 0: c.fill.fore_color.rgb = TEAL if cond else ORANGE
            else: c.fill.fore_color.rgb = RGBColor(0xE8, 0xF9, 0xF8) if cond else RGBColor(0xFF, 0xF4, 0xE6)
            p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = txt
            r.font.size = Pt(16 if i == 0 else 20); r.font.bold = (i == 0 or j == 0); r.font.name = 'Arial'
            r.font.color.rgb = WHITE if (i == 0 or j == 0) else NAVY
    text_box(sl, x0, y0 - 0.38, cw0 + 8 * cw, 0.32, 'כללים (Rules)', 13, TEAL, True, align=PP_ALIGN.CENTER, name='Rules label')
    tb = sl.shapes.add_textbox(Inches(8.0), Inches(2.4), Inches(3.9), Inches(2.6)); tb.name = 'Legend'
    tf = tb.text_frame; tf.word_wrap = True
    leg = [('תנאים (Conditions)', TEAL, True), ('C1 – דירה קטנה', BODY, False), ('C2 – דירה גדולה', BODY, False), ('C3 – אזעקה', BODY, False),
           ('פעולות (Actions)', ORANGE, True), ('A1, A2', BODY, False)]
    for k, (t, col, b) in enumerate(leg):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph(); p.alignment = PP_ALIGN.RIGHT
        if b and k: p.space_before = Pt(14)
        r = p.add_run(); r.text = t; r.font.size = Pt(18 if not b else 16); r.font.bold = b; r.font.color.rgb = col; r.font.name = 'Arial'

    # --- slide 89: mind map redrawn (the picture was too blurry to read)
    sl = P.slides[88]
    pic = [s for s in sl.shapes if s.name == 'Figure'][0]
    pic._element.getparent().remove(pic._element)
    LW, MW, CW, H = 1.12, 0.92, 1.1, 0.34
    xL, xM, xC, xR, xRL = 0.72, 1.98, 2.98, 4.18, 5.2
    br = {'sub': (RGBColor(0xFF, 0xF3, 0xC4), RGBColor(0xC9, 0x9A, 0x06)), 'hdr': (RGBColor(0xE3, 0xF6, 0xEC), RGBColor(0x12, 0xA3, 0x7A)),
          'side': (RGBColor(0xFD, 0xE6, 0xCF), RGBColor(0xE0, 0x7A, 0x0B)), 'foot': (RGBColor(0xFB, 0xE0, 0xE6), RGBColor(0xC2, 0x2E, 0x5F))}
    made = []
    cy = 4.05
    web = node(sl, xC, cy - 0.24, CW, 0.48, 'Website', NAVY, NAVY, WHITE, 13, True, name='MM Website')
    home = node(sl, xC, 1.62, CW, H, 'Home Page', RGBColor(0xDF, 0xEF, 0xFA), RGBColor(0x2F, 0x7E, 0xC1), NAVY, 10, True, name='MM Home')
    made += [arrow(sl, xC + CW / 2, cy - 0.24, xC + CW / 2, 1.62 + H, RGBColor(0x2F, 0x7E, 0xC1))]
    def branch(key, label, mx, my, leaves, lx, left):
        fill, line = br[key]
        m = node(sl, mx, my - 0.19, MW, 0.38, label, fill, line, NAVY, 10.5, True, name='MM ' + label)
        a = arrow(sl, xC if left else xC + CW, cy, mx + MW if left else mx, my, line); made.append(a)
        for k, (t, ly) in enumerate(leaves):
            node(sl, lx, ly - H / 2, LW, H, t, fill, line, NAVY, 9.5, name='MM ' + t)
            made.append(arrow(sl, mx if left else mx + MW, my, lx + LW if left else lx, ly, line))
    branch('sub', 'Sub Pages', xM, 2.95, [('Projects', 2.3), ('Board Info', 2.74), ('Branches', 3.18), ('Customers', 3.62)], xL, True)
    branch('foot', 'Footer', xM, 5.25, [('Navigation Links', 4.8), ('Images', 5.25), ('Privacy Policy', 5.7)], xL, True)
    branch('hdr', 'Header', xR, 2.75, [('Logo', 2.3), ('Navigation Links', 2.75), ('Social Icons', 3.2)], xRL, False)
    branch('side', 'Side Bar', xR, 5.25, [('Search', 4.4), ('Contact Info', 4.83), ('Newsletter Box', 5.26), ('RSS options', 5.69), ('Recent Blog Posts', 6.12)], xRL, False)
    send_back(sl, made)
    card = [s for s in sl.shapes if s.name == 'Figure Card'][0]; send_back(sl, [card])

if N == 5:
    for n in (17, 19):
        sl = P.slides[n - 1]
        for s in walk(sl.shapes):
            if not s.has_text_frame: continue
            t = s.text_frame.text.strip()
            if abs(s.top / 914400 - 3.1) < 0.02 and abs(s.height / 914400 - 0.83) < 0.02:
                set_size(s, 18 if t == 'Done' else 16, True)
            elif t in ('משימה בפיתוח', 'משימות בפיתוח'):
                set_size(s, 11, True, True)
            elif t.startswith('משימה שהפיתוח'):
                set_size(s, 9.5, True, True)

if N == 2:
    sl = P.slides[10]
    tb = [x for x in walk(sl.shapes) if x.has_text_frame and x.text_frame.text.strip() == 'Verification / Testing'][0]
    tb.left = tb.left - 420000
    tb.text_frame.word_wrap = False

if N == 1:
    sl = P.slides[54]
    c = [x for x in sl.shapes if x.has_text_frame and x.text_frame.text.startswith('בדיקות שליליות')][0]
    bp = c.text_frame._txBody.find(qn('a:bodyPr'))
    for ch in list(bp):
        if ch.tag in (qn('a:normAutofit'), qn('a:spAutoFit')): bp.remove(ch)
    set_size(c, 14, True)
    c.text_frame.margin_top = c.text_frame.margin_bottom = Inches(0.04)
P.save(sys.argv[3])
