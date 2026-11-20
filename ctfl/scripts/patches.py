#!/usr/bin/env python3
"""per-slide patches requested by the user. usage: patches.py N in.pptx out.pptx
slide numbers are the user's (pre-deletion) numbering."""
import sys, re, copy, os, subprocess, shutil, json
from lxml import etree
from pk import *

N = int(sys.argv[1])
D = Deck(N, sys.argv[2])
ns = D.ns


def src_text_els(i):
    t = D.stree(i)
    cls, tel, nel, rest = classify(t)
    return t, tel, nel, rest


def models(i, kinds=('textplain',), drop=None):
    t, tel, nel, rest = src_text_els(i)
    els = [e for k, e in rest if k in kinds]
    ms = [m for m in ns['extract_paras'](els) if m]
    if drop:
        ms = [m for m in ms if not drop(m)]
    return ms


def rebuild(i, ms, layouts, y0=None, extra=()):
    """re-lay out text models on slide i with one of the given layout names"""
    old = ns['Y0']
    if y0 is not None:
        ns['Y0'] = y0
    try:
        ms2, groups = ns['analyse'](ms)
        ctx = {'title': '', 'body': ' '.join(m['text'] for m in ms2), 'counter': {}, 'ms': ms2, 'groups': groups}
        ids = D.ids(i)
        fns = {'cols': lambda: ns['L_cols'](ids, D.slides[i - 1], ctx), 'timeline': lambda: ns['L_timeline'](ids, D.slides[i - 1], ctx),
               'accordion': lambda: ns['L_accordion'](ids, D.slides[i - 1], ctx), 'cards0': lambda: ns['L_cards'](ids, D.slides[i - 1], ctx, 0),
               'cards1': lambda: ns['L_cards'](ids, D.slides[i - 1], ctx, 1), 'plain': lambda: ns['L_plain'](ids, D.slides[i - 1], ctx),
               'illus_l': lambda: ns['L_list_illus'](ids, D.slides[i - 1], ctx, 'left'), 'band': lambda: ns['L_intro_band'](ids, D.slides[i - 1], ctx)}
        for l in layouts:
            r = fns[l]()
            if r and all(x is not None for x in r):
                D.clear(i)
                D.add(i, list(extra) + r)
                return l
        raise Exception(f'no layout fits slide {i}')
    finally:
        ns['Y0'] = old


def heading(ids, text_, y, pt=26, color=NAVY, x0=None, x1=None):
    x0 = ns['X0'] if x0 is None else x0
    x1 = ns['X1'] if x1 is None else x1
    w = wlen(text_, pt, 1) + 0.3
    cx = (x0 + x1) / 2
    return [sp_xml(ids, 'Heading', x0, y, x1 - x0, 0.55, anchor='ctr', ins=(0, 0, 0, 0), txbox=True,
                   body=simple_para(text_, pt, color, True, 'ctr', bool(HEB.search(text_)))),
            sp_xml(ids, 'Heading Rule', cx - 0.6, y + 0.6, 1.2, 0.06, 'rect', fill=TEAL)]


def section_slide(i, num, head, topic, kicker='הנושא הבא'):
    ids = D.ids(i)
    X0, X1, Y0, Y1 = ns['X0'], ns['X1'], ns['Y0'], ns['Y1']
    D.clear(i)
    rid = D.illus(i, topic, 2)
    s = 3.3 if D.wide else 2.6
    body = simple_para(kicker, 18, TEAL, True, 'r', True) + simple_para(num, 72 if D.wide else 56, TEAL, True, 'r', False) + \
        simple_para(head, 40 if D.wide else 32, 'FFFFFF', True, 'r', True)
    D.add(i, [sp_xml(ids, 'Section Panel', X0, Y0 + 0.05, X1 - X0, Y1 - Y0 - 0.05, 'roundRect', fill=NAVY, adj={'adj': 5000}),
              sp_xml(ids, 'Section Disc', X0 + 0.6, Y0 + (Y1 - Y0 - s - 0.3) / 2, s + 0.3, s + 0.3, 'ellipse', fill='FFFFFF'),
              pic_xml(ids, rid, X0 + 0.75, Y0 + (Y1 - Y0 - s) / 2, s, s),
              sp_xml(ids, 'Section Text', X0 + s + 1.4, Y0 + 0.4, X1 - X0 - s - 2.0, Y1 - Y0 - 0.8, anchor='ctr', ins=(0.1, 0.1, 0.4, 0.1),
                     txbox=True, body=body),
              sp_xml(ids, 'Section Bar', X1 - 0.25, Y0 + 1.2, 0.1, Y1 - Y0 - 2.4, 'rect', fill=ORANGE)])


def cover_title(i, txt):
    ids = D.ids(i)
    D.add(i, [sp_xml(ids, 'Part Title', D.W * 0.52, D.H * 0.4, D.W * 0.44, 1.1, anchor='ctr', txbox=True,
                     body=simple_para(txt, 40 if D.wide else 32, 'FFFFFF', True, 'r', True))])


def strip_para_prefix(i, pat):
    for p in D.tree(i).iter(A + 'p'):
        ts = [t for t in p.iter(A + 't')]
        full = ''.join(t.text or '' for t in ts)
        m = re.match(pat, full)
        if not m:
            continue
        cut = m.end()
        for t in ts:
            if cut <= 0:
                break
            L = len(t.text or '')
            if L <= cut:
                cut -= L
                t.text = ''
            else:
                t.text = t.text[cut:]
                cut = 0


def fit_content_above(i, bottom, top=None, names_skip=KEEP):
    """vertically compress content shapes so nothing goes below `bottom`"""
    tr = D.sptree(i)
    els = []
    for el in tr:
        nv = el.find('.//' + P + 'cNvPr')
        if nv is None or (nv.get('name') or '') in names_skip:
            continue
        b = box(el)
        if b:
            els.append((el, b))
    if not els:
        return
    t0 = top if top is not None else min(b[1] for _, b in els)
    b1 = max(b[1] + b[3] for _, b in els)
    if b1 <= bottom:
        return
    k = (bottom - t0) / (b1 - t0)
    for el, b in els:
        xf = el.find(P + 'spPr/' + A + 'xfrm')
        if xf is None:
            xf = el.find(P + 'grpSpPr/' + A + 'xfrm')
        if xf is None:
            xf = el.find(P + 'xfrm')
        o, e = xf.find(A + 'off'), xf.find(A + 'ext')
        ny = t0 + (b[1] - t0) * k
        o.set('y', str(emu(ny)))
        e.set('cy', str(emu(b[3] * k)))


# =====================================================================
def deck1():
    # 66, 67: centred 'Test execution' heading, without the digit
    for i in (66, 67):
        ms = models(i)
        ms = [m for m in ms if not re.match(r'^\s*6\.\s*Test execution\s*$', m['text'])]
        ids = D.ids(i)
        rebuild(i, ms, ['cols', 'timeline', 'plain'] if i == 67 else ['timeline', 'cols', 'plain'], y0=2.05,
                extra=heading(ids, 'Test execution', 1.22, 28, NAVY))
    # 72: section slide for 1.4.5
    section_slide(72, '1.4.5', 'תפקידים בבדיקות', 'roles')
    # 84: independence ladder with a visible scale arrow
    D.clear(84, KEEP + ('Section Number',))
    ids = D.ids(84)
    items = ['אין עצמאות של הבדיקות - המפתח בודק את הקוד שהוא כתב', 'עצמאות נמוכה מפתח אחר מצוות הפיתוח בודק את הקוד',
             'עצמאות גבוהה צוות בדיקות עצמאי מחוץ לפיתוח אך בתוך הארגון', 'עצמאות גבוהה מאוד בודקים חיצוניים לארגון']
    cols = [NAVY, TEAL_D, TEAL, ORANGE]
    out = []
    top, rh, gap = 1.45, 1.13, 0.17
    for k, t in enumerate(items):
        y = top + k * (rh + gap)
        x1 = 12.3 - k * 0.55
        x0 = 3.0
        out.append(sp_xml(ids, f'Level {k + 1}', x0, y, x1 - x0, rh, 'roundRect', fill=cols[k], adj={'adj': 30000}, anchor='ctr',
                          ins=(0.3, 0.03, 1.0, 0.03), body=simple_para(t, 20, 'FFFFFF' if k != 2 else NAVY, True, 'r', True)))
        out.append(sp_xml(ids, f'Level Num {k + 1}', x1 - 0.85, y + (rh - 0.62) / 2, 0.62, 0.62, 'ellipse', fill='FFFFFF', anchor='ctr',
                          ins=(0, 0, 0, 0), body=simple_para(f'{k + 1:02d}', 15, cols[k] if k != 2 else TEAL_D, True, 'ctr', False)))
    ah = 4 * rh + 3 * gap
    out.append(sp_xml(ids, 'Scale Arrow', 1.35, top + 0.45, 0.9, ah - 0.9, 'downArrow', fill=TINT, line=TEAL_D, lw=1.5,
                      adj={'adj1': 50000, 'adj2': 40000}))
    out.append(sp_xml(ids, 'Scale Top', 0.55, top - 0.05, 2.5, 0.45, anchor='ctr', txbox=True, body=simple_para('לא עצמאי', 16, NAVY, True, 'ctr', True)))
    out.append(sp_xml(ids, 'Scale Bottom', 0.55, top + ah - 0.4, 2.5, 0.45, anchor='ctr', txbox=True, body=simple_para('עצמאי', 16, OR_D, True, 'ctr', True)))
    D.add(84, out)


# =====================================================================
def vmodel(ids, x, y, w, h, static=False):
    """native V-model: development (left) / testing (right) with review + integration callouts"""
    out = []
    L = ['Business Requirements', 'High-Level Design', 'Low-Level Design']
    Rr = ['Acceptance Tests', 'System Tests', 'Integration Tests']
    bw, bh = 2.3, 0.5
    top = y + 0.75
    step = (h - 1.75) / 3
    inset = 0.85
    lx = [x + 1.6 + k * inset for k in range(3)]
    rx = [x + w - bw - 2.3 - k * inset for k in range(3)]
    for k in range(3):
        by = top + k * step
        out.append(box_t(ids, f'Dev {k + 1}', lx[k], by, bw, bh, L[k], NAVY, 'FFFFFF', 13))
        out.append(box_t(ids, f'Test {k + 1}', rx[k], by, bw, bh, Rr[k], TEAL_D, 'FFFFFF', 13))
        out.append(line_xml(ids, rx[k] - 0.05, by + bh / 2, lx[k] + bw + 0.05, by + bh / 2, ORANGE, 1.5, tail='triangle', dash='dash'))
        if k < 2:
            out.append(line_xml(ids, lx[k] + bw / 2, by + bh, lx[k + 1] + bw / 2, by + step, GRAY, 2, tail='triangle'))
            out.append(line_xml(ids, rx[k + 1] + bw / 2, by + step, rx[k] + bw / 2, by + bh, GRAY, 2, tail='triangle'))
        out.append(label(ids, x + 0.2, by + bh / 2 - 0.2, 1.3, 0.4, 'Review', 13, OR_D if static else GRAY, True))
    cy = top + 3 * step
    cw = 3.2
    cx0 = x + (w - cw) / 2 - 0.6
    out.append(box_t(ids, 'Code', cx0, cy, cw / 2 - 0.1, bh, 'Code', ORANGE, 'FFFFFF', 13))
    out.append(box_t(ids, 'Unit Tests', cx0 + cw / 2 + 0.1, cy, cw / 2 - 0.1, bh, 'Unit Tests', TEAL_D, 'FFFFFF', 13))
    out.append(line_xml(ids, cx0 + cw / 2 + 0.08, cy + bh / 2, cx0 + cw / 2 - 0.08, cy + bh / 2, ORANGE, 1.5, tail='triangle', dash='dash'))
    out.append(line_xml(ids, lx[2] + bw / 2, top + 2 * step + bh, cx0 + 0.4, cy, GRAY, 2, tail='triangle'))
    out.append(line_xml(ids, cx0 + cw - 0.4, cy, rx[2] + bw / 2, top + 2 * step + bh, GRAY, 2, tail='triangle'))
    out.append(label(ids, x + 0.2, cy + bh / 2 - 0.2, 1.3, 0.4, 'Code review' if static else 'Review', 13, OR_D if static else GRAY, True))
    # integration callouts (right)
    out.append(box_t(ids, 'System Integration', x + w - 1.95, top + step + 0.0, 1.9, 0.62, 'System\nIntegration', 'FFFFFF', NAVY, 12, line=NAVY))
    out.append(line_xml(ids, x + w - 1.95, top + step + 0.31, rx[1] + bw + 0.05, top + step + bh / 2, NAVY, 1.25, tail='oval'))
    out.append(box_t(ids, 'Component Integration', x + w - 1.95, cy - 0.15, 1.9, 0.62, 'Component\nIntegration', 'FFFFFF', OR_D, 12, line=ORANGE))
    out.append(line_xml(ids, x + w - 1.95, cy + 0.16, cx0 + cw + 0.05, cy + bh / 2, ORANGE, 1.25, tail='oval'))
    # static / dynamic brackets
    out.append(sp_xml(ids, 'Static Bracket', x + 1.45, top, 0.12, cy + bh - top, 'leftBracket', line=TEAL_D, lw=2))
    out.append(box_t(ids, 'Static', x, y + h - 0.55, 2.3, 0.5, 'Static testing', TINT, NAVY, 13))
    out.append(box_t(ids, 'Dynamic', x + w - 2.6, y + h - 0.55, 2.5, 0.5, 'Dynamic testing', 'FDE7CC', OR_D, 13))
    out.append(label(ids, x + (w - 5) / 2 - 0.6, y + h - 0.55, 5, 0.5, 'V-Model : Development & Testing', 14, NAVY, True))
    return out


def box_t(ids, name, x, y, w, h, txt, fill, color, pt, geom='roundRect', line=None):
    body = ''.join(simple_para(t, pt, color, True, 'ctr', bool(HEB.search(t))) for t in txt.split('\n'))
    return sp_xml(ids, name, x, y, w, h, geom, fill=fill, line=line, anchor='ctr', ins=(0.05, 0.02, 0.05, 0.02), body=body,
                  adj={'adj': 18000} if geom == 'roundRect' else None)


def label(ids, x, y, w, h, txt, pt=12, color=BODY, bold=False, algn='ctr'):
    body = ''.join(simple_para(t, pt, color, bold, algn, bool(HEB.search(t))) for t in txt.split('\n'))
    return sp_xml(ids, 'Label', x, y, w, h, anchor='ctr', ins=(0.02, 0, 0.02, 0), body=body, txbox=True)


def rich_box(ids, name, x, y, w, h, ms, pt, color=BODY, algn=None, anchor='t', bold=None, fill=None, line=None, ins=(0.1, 0.05, 0.1, 0.05), geom='rect', before=4, bullet=None):
    body = ''.join(ns['para_xml'](m, pt, color, bullet, TEAL, indent=0.02 if bullet else 0, algn=algn, bold=bold, before=before if k else 0)
                   for k, m in enumerate(ms))
    return sp_xml(ids, name, x, y, w, h, geom, fill=fill, line=line, anchor=anchor, ins=ins, txbox=True, body=body, adj={'adj': 8000} if geom == 'roundRect' else None)


def fitpt(ms, w, h, mx, mn, spacing=0.3):
    items = [{'m': m, 'kind': 'plain'} for m in ms]
    return ns['fit_items'](items, w, h, mx, mn, ins=(0.1, 0.05, 0.1, 0.05), spacing=spacing) or mn


def deck2():
    # 15: native V-model
    D.clear(15)
    ids = D.ids(15)
    out = vmodel(ids, 0.55, 1.3, 12.25, 5.5)
    out.append(box_t(ids, 'Validation', 0.6, 1.25, 3.6, 0.62, "Validation = 'Are you building\nthe right thing?'", 'FFFFFF', TEAL_D, 12, line=TEAL_D))
    out.append(box_t(ids, 'Verification', 8.0, 1.25, 3.6, 0.62, "Verification = 'Are you\nbuilding the thing right?'", 'FFFFFF', TEAL_D, 12, line=TEAL_D))
    D.add(15, out)
    # 69-80: no running principle numbers
    for i in range(69, 81):
        strip_para_prefix(i, r'^\s*\d{1,2}\.\s*')
    # 28: XP middle circle as cards
    ms = models(28)
    top = min(m['lvl'] for m in ms)
    gs = []
    for m in ms:
        if m['lvl'] == top:
            gs.append([m, []])
        else:
            gs[-1][1].append(m)
    D.clear(28)
    ids = D.ids(28)
    pos = ns['card_grid'](ids, len(gs), ns['Y0'] + 0.05, ns['Y1'], 2)
    out = []
    acc = [TEAL, ORANGE, NAVY, TEAL_D]
    for k, ((hm, subs), (x, y, w, h)) in enumerate(zip(gs, pos)):
        out.append(sp_xml(ids, f'Card {k + 1}', x, y, w, h, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 6000}, shadow=True))
        out.append(sp_xml(ids, f'Card Accent {k + 1}', x + w - 0.1, y + 0.2, 0.1, h - 0.4, 'rect', fill=acc[k % 4]))
        out.append(sp_xml(ids, f'Card Icon {k + 1}', x + w - 0.85, y + 0.25, 0.55, 0.55, 'ellipse', fill=acc[k % 4], anchor='ctr', ins=(0, 0, 0, 0),
                          body=simple_para(str(k + 1), 16, 'FFFFFF', True, 'ctr', False)))
        hh = 1.05
        out.append(rich_box(ids, f'Card Title {k + 1}', x + 0.2, y + 0.18, w - 1.15, hh, [hm], fitpt([hm], w - 1.15, hh, 18, 13), NAVY, anchor='ctr'))
        if subs:
            bh = h - hh - 0.4
            out.append(rich_box(ids, f'Card Text {k + 1}', x + 0.2, y + hh + 0.25, w - 0.45, bh, subs, fitpt(subs, w - 0.6, bh, 17, 11), BODY,
                                bullet='sq', before=4))
    D.add(28, out)
    # 123: top-down styled like bottom-up
    ms = models(123)
    bu = [k for k, m in enumerate(ms) if 'Bottom-UP' in m['text'] or 'Bottom-Up' in m['text']][0]
    td = [k for k, m in enumerate(ms) if 'Top-down' in m['text'] or 'Top-Down' in m['text']][0]
    D.clear(123)
    ids = D.ids(123)
    X0, X1 = ns['X0'], ns['X1']
    out = []
    y = 1.32
    for k, (hk, body) in enumerate([(bu, [m for j, m in enumerate(ms) if bu < j < td]), (td, [m for j, m in enumerate(ms) if j > td])]):
        rid = D.illus(123, 'levels', k)
        out.append(rich_box(ids, f'Approach {k + 1}', X0, y, X1 - X0, 0.95, [ms[hk]], 18, 'FFFFFF', anchor='ctr', fill=NAVY if k == 0 else TEAL_D,
                            geom='roundRect', ins=(1.25, 0.05, 0.3, 0.05)))
        out.append(pic_xml(ids, rid, X0 + 0.15, y + 0.08, 0.8, 0.8))
        y += 1.08
        if body:
            h = 0.36 * len(body) + 0.1
            out.append(rich_box(ids, f'Approach Body {k + 1}', X0 + 0.3, y, X1 - X0 - 0.3, h, body, 16, BODY, bullet='sq', before=2))
            y += h + 0.25
    D.add(123, out)
    # 147: performance testing hub
    D.clear(147)
    ids = D.ids(147)
    cx, cy = 6.67, 4.05
    out = [sp_xml(ids, 'Hub Ring', cx - 2.15, cy - 2.15, 4.3, 4.3, 'ellipse', line=TINT, lw=14),
           sp_xml(ids, 'Hub', cx - 1.35, cy - 1.35, 2.7, 2.7, 'ellipse', fill=NAVY, anchor='ctr',
                  body=simple_para('Performance', 18, 'FFFFFF', True, 'ctr', False) + simple_para('testing', 18, TEAL, True, 'ctr', False))]
    tops = [('Load', 'perf', cx + 2.55, 1.45, TEAL_D), ('Stress', 'risk', cx - 2.55 - 3.4, 1.45, ORANGE), ('Volume', 'data', cx - 1.7, 5.3, NAVY)]
    for k, (t, tp, x, y, c) in enumerate(tops):
        w = 3.4
        out.append(sp_xml(ids, f'{t} Card', x, y, w, 1.25, 'roundRect', fill='FFFFFF', line=c, lw=2.5, adj={'adj': 22000}, shadow=True))
        rid = D.illus(147, tp, k)
        out.append(pic_xml(ids, rid, x + w - 1.15, y + 0.12, 1.0, 1.0))
        out.append(sp_xml(ids, f'{t} Label', x + 0.15, y, w - 1.35, 1.25, anchor='ctr', txbox=True, body=simple_para(t, 28, c, True, 'ctr', False)))
    out.append(line_xml(ids, cx + 0.95, cy - 0.95, cx + 2.55 + 0.5, 1.45 + 1.25, TEAL_D, 2.5, head='oval'))
    out.append(line_xml(ids, cx - 0.95, cy - 0.95, cx - 2.55 - 0.5, 1.45 + 1.25, ORANGE, 2.5, head='oval'))
    out.append(line_xml(ids, cx, cy + 1.35, cx, 5.3, NAVY, 2.5, head='oval'))
    D.add(147, out)


def deck3():
    # 4: native static-testing V model
    D.clear(4)
    D.add(4, vmodel(D.ids(4), 0.55, 1.3, 12.25, 5.5, static=True))
    # 37: big cards, notes inside
    ms = models(37)
    _, gg = ns['analyse'](ms)
    groups = [[g[2] if g[2] is not None else g[1][0], g[1] if g[2] is not None else g[1][1:]] for g in gg]
    D.clear(37)
    ids = D.ids(37)
    X0, X1, Y0, Y1 = ns['X0'], ns['X1'], ns['Y0'], ns['Y1']
    n = len(groups)
    cols = 3 if n > 4 else 2
    pos = ns['card_grid'](ids, n, Y0 + 0.05, Y1, cols)
    out = []
    accents = [TEAL, ORANGE, NAVY]
    for k, ((hm, notes), (x, y, w, h)) in enumerate(zip(groups, pos)):
        out.append(sp_xml(ids, f'Card {k + 1}', x, y, w, h, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 6000}, shadow=True))
        out.append(sp_xml(ids, f'Card Bar {k + 1}', x, y, w, 0.14, 'rect', fill=accents[k % 3]))
        out.append(sp_xml(ids, f'Card Num {k + 1}', x + w - 0.75, y + 0.3, 0.55, 0.55, 'ellipse', fill=accents[k % 3], anchor='ctr', ins=(0, 0, 0, 0),
                          body=simple_para(str(k + 1), 16, 'FFFFFF', True, 'ctr', False)))
        nh = 1.0 if notes else 0
        out.append(rich_box(ids, f'Card Title {k + 1}', x + 0.2, y + 0.3, w - 1.05, h - 0.5 - nh * (h * 0.42), [hm], 19, NAVY, anchor='ctr' if not notes else 't', bold=True))
        if notes:
            ny = y + h * 0.55
            out.append(rich_box(ids, f'Card Note {k + 1}', x + 0.2, ny, w - 0.4, y + h - ny - 0.2, notes, 15, BODY, anchor='ctr', fill=SOFT,
                                geom='roundRect', ins=(0.15, 0.08, 0.15, 0.08)))
    D.add(37, out)


# =====================================================================
def notebook(i):
    """ch4 notebook slides -> side callout (definition / band label / key text) + main text"""
    t = D.stree(i)
    cls, tel, nel, rest = classify(t)
    cards = [(e, box(e)) for k, e in rest if k == 'shape' and box(e) and box(e)[2] > 3 and box(e)[3] > 4]
    cb = max(cards, key=lambda c: c[1][2] * c[1][3])[1]
    inside = lambda b: cb[0] <= b[0] + b[2] / 2 <= cb[0] + cb[2] and cb[1] <= b[1] + b[3] / 2 <= cb[1] + cb[3]
    bands = [box(e) for k, e in rest if k == 'shape' and box(e) and inside(box(e)) and 0.6 < box(e)[3] < 1.6 and box(e)[2] > 3]
    band = bands[0] if bands else [cb[0], cb[1] + cb[3] * 0.33, cb[2], 1.1]
    top, bot, main, lab, pics = [], [], [], [], []
    for k, e in rest:
        b = box(e)
        if not b:
            continue
        tx = text(e).strip()
        if k == 'pic' and inside(b):
            pics.append(e)
            continue
        if not tx or re.match(r'^\s*פרק\s*\d', tx):
            continue
        if inside(b):
            cy = b[1] + b[3] / 2
            if band[1] <= cy <= band[1] + band[3]:
                lab.append(tx)
            elif cy < band[1]:
                top.append(e)
            else:
                bot.append(e)
        elif k in ('textplain', 'boxed', 'shapetext'):
            main.append(e)
    defin = [m for m in ns['extract_paras'](top) if m]
    key = [m for m in ns['extract_paras'](bot) if m]
    mainm = [m for m in ns['extract_paras'](main) if m]
    label_txt = ' '.join(lab).strip() or 'רעיון מרכזי'
    D.clear(i)
    ids = D.ids(i)
    X0, X1, Y0, Y1 = ns['X0'], ns['X1'], ns['Y0'], ns['Y1']
    cw = 4.6
    cx = X1 - cw
    out = []
    y = Y0 + 0.05
    if defin or pics:
        h = 1.75
        if defin:
            pt = fitpt(defin, cw - 0.45, h - 0.15, 18, 11)
            out.append(rich_box(ids, 'Definition', cx, y, cw, h, defin, pt, NAVY, anchor='ctr', fill=TINT, geom='roundRect', ins=(0.2, 0.08, 0.25, 0.08)))
        else:
            out.append(sp_xml(ids, 'Figure Card', cx, y, cw, h, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 8000}))
            out.append(D.copy_src_pic(i, pics[0], cx + 0.15, y + 0.1, cw - 0.3, h - 0.2))
        y += h + 0.15
    rid = D.illus(i, 'learn', i % 3)
    out.append(sp_xml(ids, 'Key Idea Band', cx, y, cw, 0.62, 'roundRect', fill=NAVY, adj={'adj': 50000}, anchor='ctr', ins=(0.1, 0, 0.75, 0),
                      body=simple_para(label_txt, 20, 'FFFFFF', True, 'r', True)))
    out.append(pic_xml(ids, rid, cx + 0.12, y + 0.04, 0.54, 0.54))
    y += 0.75
    if key:
        h = Y1 - y
        pt = fitpt(key, cw - 0.45, h - 0.2, 22, 12)
        out.append(rich_box(ids, 'Key Idea', cx, y, cw, h, key, pt, BODY, anchor='ctr', fill='FFFFFF', line=ORANGE, geom='roundRect',
                            ins=(0.2, 0.1, 0.25, 0.1)))
    if mainm:
        mw = cx - 0.35 - X0
        items = ns['flat_items'](mainm)
        tb, pt = ns['text_block'](ids, 'Body', X0, Y0 + 0.05, mw, Y1 - Y0 - 0.05, items, 20, 9, anchor='ctr', fill='FFFFFF', line=LINE,
                                  geom='roundRect', ins=(0.3, 0.2, 0.35, 0.2), adj={'adj': 4000}, shadow=True)
        out.insert(0, tb)
    D.add(i, out)


def state_node(ids, name, cx, cy, r, txt, fill=NAVY, color='FFFFFF', pt=14):
    return sp_xml(ids, name, cx - r, cy - r, 2 * r, 2 * r, 'ellipse', fill=fill, line='FFFFFF', lw=2, anchor='ctr', ins=(0, 0, 0, 0),
                  body=simple_para(txt, pt, color, True, 'ctr', bool(HEB.search(txt))))


def arc(ids, x1, y1, x2, y2, color=GRAY, lw=2.25, lab=None, lx=None, ly=None, lpt=12, lcol=None):
    out = [line_xml(ids, x1, y1, x2, y2, color, lw, tail='triangle')]
    if lab:
        out.append(label(ids, lx - 1.3, ly - 0.2, 2.6, 0.4, lab, lpt, lcol or color, True))
    return out


def toggle_icon(i, on):
    return D.media(i, f'assets/toggle_{"on" if on else "off"}.png')


def deck4():
    for i in (16, 26, 38, 42, 43):
        notebook(i)
    X0, X1, Y0, Y1 = ns['X0'], ns['X1'], ns['Y0'], ns['Y1']
    # 39: what is a state transition (concept diagram)
    D.clear(39)
    ids = D.ids(39)
    out = heading(ids, 'מעבר בין מצבים (State Transition)', Y0 + 0.0, 24, NAVY)
    cx = 6.9
    out += [box_t(ids, 'State 1', cx - 1.3, 2.25, 2.6, 0.75, 'מצב 1', NAVY, 'FFFFFF', 20),
            box_t(ids, 'State 2', cx - 1.3, 5.75, 2.6, 0.75, 'מצב 2', TEAL_D, 'FFFFFF', 20),
            line_xml(ids, cx, 3.0, cx, 5.75, NAVY, 3, tail='triangle'),
            line_xml(ids, cx - 1.1, 4.35, cx + 1.1, 4.35, ORANGE, 3),
            box_t(ids, 'Transition', cx + 1.35, 4.05, 1.8, 0.6, 'מעבר', ORANGE, 'FFFFFF', 18),
            label(ids, cx - 2.9, 3.7, 1.9, 0.45, 'אירוע', 18, NAVY, True),
            label(ids, cx - 2.9, 4.6, 1.9, 0.45, 'פעולה', 18, NAVY, True),
            box_t(ids, 'Input', 1.6, 3.65, 2.0, 0.55, 'קלט', TINT, NAVY, 18),
            box_t(ids, 'Output', 1.6, 4.55, 2.0, 0.55, 'פלט', 'FDE7CC', OR_D, 18),
            line_xml(ids, 3.6, 3.92, cx - 2.9, 3.92, GRAY, 2, tail='triangle'),
            line_xml(ids, cx - 2.9, 4.82, 3.6, 4.82, GRAY, 2, tail='triangle'),
            line_xml(ids, cx - 1.05, 3.92, cx - 0.05, 4.3, GRAY, 1.25, dash='dash'),
            line_xml(ids, cx - 1.05, 4.82, cx - 0.05, 4.4, GRAY, 1.25, dash='dash')]
    rid = D.illus(39, 'process', 1)
    out.append(pic_xml(ids, rid, 10.0, 2.6, 2.6, 2.6))
    D.add(39, out)

    # 40 / 41: switch examples (OFF->ON and ON->OFF)
    for i, (frm, to, inp, outp) in ((40, ('OFF', 'ON', 'switch on', 'light on')), (41, ('ON', 'OFF', 'switch off', 'light off'))):
        D.clear(i)
        ids = D.ids(i)
        on_first = frm == 'ON'
        out = [sp_xml(ids, 'Example Card', X0, Y0 + 0.1, X1 - X0, Y1 - Y0 - 0.1, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 4000}, shadow=True)]
        out.append(pic_xml(ids, toggle_icon(i, on_first), 1.2, 2.35, 2.6, 2.6 * 0.6))
        out.append(label(ids, 1.0, 4.1, 3.0, 0.5, 'Switch', 16, GRAY, True))
        out.append(line_xml(ids, 4.4, 2.0, 4.4, 6.2, LINE, 1.5))
        a = (6.4, 4.0)
        b = (10.6, 4.0)
        out.append(state_node(ids, 'From', a[0], a[1], 0.85, frm, NAVY if frm == 'OFF' else TEAL_D, 'FFFFFF', 22))
        out.append(state_node(ids, 'To', b[0], b[1], 0.85, to, TEAL_D if to == 'ON' else NAVY, 'FFFFFF', 22))
        out.append(line_xml(ids, a[0] + 0.9, a[1], b[0] - 0.9, b[1], ORANGE, 3, tail='triangle'))
        out.append(rich_like := sp_xml(ids, 'IO', 7.45, 4.45, 3.0, 1.0, anchor='t', txbox=True,
                                       body=simple_para(f'Input:   {inp}', 15, NAVY, True, 'l', False) + simple_para(f'Output: {outp}', 15, OR_D, True, 'l', False)))
        D.add(i, out)

    # 44: transition tree example
    D.clear(44)
    ids = D.ids(44)
    out = [label(ids, X0, Y0, X1 - X0, 0.5, 'עץ מעברים דוגמה', 22, TEAL_D, True, 'r')]
    # left: state graph
    g = [('OFF', 2.2, 2.6), ('ON', 2.2, 5.6), ('FAULT', 5.0, 4.1)]
    out += [state_node(ids, 'G OFF', 2.2, 2.6, 0.62, 'OFF', NAVY), state_node(ids, 'G ON', 2.2, 5.6, 0.62, 'ON', TEAL_D),
            state_node(ids, 'G FAULT', 5.0, 4.1, 0.7, 'FAULT', ORANGE, 'FFFFFF', 13)]
    out.append(line_xml(ids, 1.75, 3.15, 1.75, 5.05, GRAY, 2.25, tail='triangle'))
    out.append(line_xml(ids, 2.65, 5.05, 2.65, 3.15, GRAY, 2.25, tail='triangle'))
    out.append(line_xml(ids, 2.8, 5.35, 4.35, 4.45, ORANGE, 2.25, tail='triangle'))
    out.append(sp_xml(ids, 'Fault Loop', 4.6, 2.9, 0.8, 0.6, 'arc', line=ORANGE, lw=2.25, adj={'adj1': 10800000, 'adj2': 0}))
    out.append(line_xml(ids, 6.3, 1.9, 6.3, 6.6, LINE, 1.5))
    # right: tree
    tx = 10.2
    nodes = [('OFF', tx, 2.4, NAVY), ('ON', tx, 3.5, TEAL_D), ('OFF', tx, 4.6, NAVY), ('ON', tx, 5.7, TEAL_D), ('FAULT', tx - 2.3, 4.6, ORANGE)]
    for k, (t_, x_, y_, c) in enumerate(nodes):
        out.append(state_node(ids, f'T{k}', x_, y_, 0.42, t_, c, 'FFFFFF', 11 if t_ == 'FAULT' else 13))
    for (a_, b_) in ((0, 1), (1, 2), (2, 3)):
        out.append(line_xml(ids, tx, nodes[a_][2] + 0.44, tx, nodes[b_][2] - 0.44, GRAY, 2, tail='triangle'))
    out.append(line_xml(ids, tx - 0.32, 3.8, tx - 2.05, 4.3, ORANGE, 2, tail='triangle', dash='dash'))
    D.add(44, out)

    # 45: test script table (native)
    D.clear(45)
    ids = D.ids(45)
    rows = [['', 'STEP 1', 'STEP 2', 'STEP 3'], ['START STATE', 'OFF', 'ON', 'OFF'], ['INPUT', 'SWITCH ON', 'SWITCH OFF', 'SWITCH ON'],
            ['OUTPUT', 'LIGHT ON', 'LIGHT OFF', 'LIGHT ON'], ['FINISH STATE', 'ON', 'OFF', 'ON']]
    out = [label(ids, X0, Y0, X1 - X0, 0.5, 'דוגמת תסריט', 22, TEAL_D, True, 'r'), label(ids, 1.6, 1.95, 2.0, 0.5, 'TEST', 22, NAVY, True, 'l')]
    cw = [2.6, 2.4, 2.4, 2.4]
    x0 = (13.333 - sum(cw)) / 2
    y = 2.55
    for r, row in enumerate(rows):
        x = x0
        for c, v in enumerate(row):
            if r == 0 and c == 0:
                x += cw[c]
                continue
            if r == 0:
                fill, col = NAVY, 'FFFFFF'
            elif c == 0:
                fill, col = TINT, NAVY
            else:
                fill, col = ('FFFFFF' if r % 2 else SOFT), (TEAL_D if v in ('ON', 'LIGHT ON', 'SWITCH ON') else OR_D if 'OFF' in v else BODY)
            out.append(box_t(ids, f'Cell {r}{c}', x, y, cw[c], 0.72, v, fill, col, 16, 'rect', line=LINE))
            x += cw[c]
        y += 0.72
    D.add(45, out)

    # 47 + 48: digital clock example (text + diagram), delete 48
    ms = models(47)
    D.clear(47)
    ids = D.ids(47)
    tw = 5.6
    items = []
    for m in ms:
        t_ = m['text'].strip()
        if t_ in ('מצבים:', 'כפתורים:'):
            items.append({'m': m, 'kind': 'head', 'color': TEAL_D})
        elif t_.startswith('דוגמא') or re.match(r'^פרק\s*\d', t_):
            continue
        else:
            items.append({'m': m, 'kind': 'bullet' if m['lvl'] or True else 'plain'})
    tb, pt = ns['text_block'](ids, 'Body', X1 - tw, Y0 + 0.05, tw, Y1 - Y0 - 0.05, items, 17, 10, anchor='ctr', spacing=0.25)
    out = [tb]
    # clock diagram
    gx0, gx1 = X0 + 0.2, X1 - tw - 0.4
    cxl, cxr = gx0 + 1.0, gx1 - 1.0
    yt, yb = 2.35, 5.65
    n_ = [('DISPLAY\nTIME', cxl, yt, NAVY), ('ADJUST\nTIME', cxr, yt, TEAL_D), ('DISPLAY\nDATE', cxl, yb, NAVY), ('ADJUST\nDATE', cxr, yb, TEAL_D)]
    for k, (t_, x_, y_, c) in enumerate(n_):
        out.append(sp_xml(ids, f'Clock {k}', x_ - 0.9, y_ - 0.48, 1.8, 0.96, 'roundRect', fill=c, adj={'adj': 30000}, anchor='ctr', ins=(0, 0, 0, 0),
                          body=''.join(simple_para(s, 13, 'FFFFFF', True, 'ctr', False) for s in t_.split('\n'))))
    for (y_, ) in ((yt,), (yb,)):
        out.append(line_xml(ids, cxl + 0.95, y_ - 0.2, cxr - 0.95, y_ - 0.2, ORANGE, 2, tail='triangle'))
        out.append(line_xml(ids, cxr - 0.95, y_ + 0.2, cxl + 0.95, y_ + 0.2, GRAY, 2, tail='triangle'))
        out.append(label(ids, (cxl + cxr) / 2 - 0.7, y_ - 0.62, 1.4, 0.35, 'reset', 12, OR_D, True))
        out.append(label(ids, (cxl + cxr) / 2 - 0.7, y_ + 0.25, 1.4, 0.35, 'set', 12, GRAY, True))
    out.append(line_xml(ids, cxl - 0.3, yt + 0.5, cxl - 0.3, yb - 0.5, NAVY, 2, tail='triangle'))
    out.append(line_xml(ids, cxl + 0.3, yb - 0.5, cxl + 0.3, yt + 0.5, NAVY, 2, tail='triangle'))
    out.append(sp_xml(ids, 'Change Mode', cxl + 0.42, (yt + yb) / 2 - 0.2, 1.4, 0.4, anchor='ctr', txbox=True, ins=(0, 0, 0, 0),
                      body=simple_para('change mode', 12, NAVY, True, 'l', False)))
    out.insert(0, sp_xml(ids, 'Diagram Card', gx0 - 0.15, Y0 + 0.25, gx1 - gx0 + 0.3, Y1 - Y0 - 0.45, 'roundRect', fill=SOFT, adj={'adj': 5000}))
    D.add(47, out)
    D.delete(48)
    # 53 / 73 part covers
    cover_title(53, 'טכניקה קופסא לבנה')
    cover_title(73, 'טכניקה מבוססת ניסיון')


# =====================================================================
def deck5():
    X0, X1, Y0, Y1 = ns['X0'], ns['X1'], ns['Y0'], ns['Y1']
    # 6: test plan components
    t = D.stree(6)
    D.clear(6)
    ids = D.ids(6)
    parts_ = ['Test Scope', 'Test Objective', 'Test Environment', 'Test Tools', 'Risk Analysis', 'Roles &\nResponsibilities', 'Test Design']
    cx, cy = 6.67, 4.05
    out = [sp_xml(ids, 'Plan Ring', cx - 2.45, cy - 2.45, 4.9, 4.9, 'ellipse', line=TINT, lw=16)]
    import math
    n = len(parts_)
    for k, p_ in enumerate(parts_):
        a = -math.pi / 2 + 2 * math.pi * k / n
        px, py = cx + 3.65 * math.cos(a), cy + 2.45 * math.sin(a)
        c = [NAVY, TEAL_D, ORANGE, TEAL][k % 4]
        out.append(line_xml(ids, cx + 1.25 * math.cos(a), cy + 1.25 * math.sin(a), px - 1.0 * math.cos(a), py - 0.35 * math.sin(a), LINE, 2))
        out.append(sp_xml(ids, f'Part {k + 1}', px - 1.3, py - 0.42, 2.6, 0.84, 'roundRect', fill=c, adj={'adj': 50000}, anchor='ctr',
                          ins=(0.05, 0, 0.05, 0), body=''.join(simple_para(s, 15, 'FFFFFF' if c != TEAL else NAVY, True, 'ctr', False) for s in p_.split('\n'))))
    out.append(sp_xml(ids, 'Plan Hub', cx - 1.25, cy - 1.25, 2.5, 2.5, 'ellipse', fill='FFFFFF', line=ORANGE, lw=4, anchor='ctr',
                      body=simple_para('Test Plan', 24, NAVY, True, 'ctr', False)))
    D.add(6, out)
    # 7: test plan contents (7 items) as numbered cards
    t = D.stree(7)
    rects = []
    intro = []
    for sp in t.iter(P + 'sp'):
        nm = sp.find('.//' + P + 'cNvPr').get('name') or ''
        tx = text(sp).strip()
        if not tx:
            continue
        if nm.startswith('Rectangle'):
            rects.append((box(sp), [m for m in ns['extract_paras']([sp]) if m]))
        elif nm.startswith('Subtitle'):
            intro = [m for m in ns['extract_paras']([sp]) if m]
    rects.sort(key=lambda r: (0 if r[0][0] > 6 else 1, r[0][1]))
    D.clear(7)
    ids = D.ids(7)
    out = []
    y = Y0 + 0.02
    if intro:
        out.append(rich_box(ids, 'Intro', X0, y, X1 - X0, 0.6, intro, 18, OR_D, algn='ctr', anchor='ctr', bold=True))
        y += 0.8
    n = len(rects)
    rows_ = 4
    gh = 0.2
    ch = (Y1 - y - gh * (rows_ - 1)) / rows_
    cw = (X1 - X0 - 3.2 - 0.3) / 2
    rid = D.illus(7, 'plan', 0)
    out.append(sp_xml(ids, 'Halo', X0 - 0.1, (y + Y1) / 2 - 1.5, 3.0, 3.0, 'ellipse', fill=TINT))
    out.append(pic_xml(ids, rid, X0 + 0.15, (y + Y1) / 2 - 1.25, 2.5, 2.5))
    for k, (b_, ms_) in enumerate(rects):
        r, c = (k, 0) if k < 4 else (k - 4, 1)
        x = X1 - (c + 1) * cw - c * 0.3
        yy = y + r * (ch + gh)
        col = [NAVY, TEAL_D, ORANGE][k % 3]
        out.append(sp_xml(ids, f'Item {k + 1}', x, yy, cw, ch, 'roundRect', fill=SOFT, adj={'adj': 20000}))
        out.append(sp_xml(ids, f'Item Num {k + 1}', x + cw - 0.75, yy + (ch - 0.58) / 2, 0.58, 0.58, 'ellipse', fill=col, anchor='ctr', ins=(0, 0, 0, 0),
                          body=simple_para(str(k + 1), 16, 'FFFFFF', True, 'ctr', False)))
        out.append(rich_box(ids, f'Item Text {k + 1}', x + 0.1, yy, cw - 0.95, ch, ms_, 17, NAVY, anchor='ctr', bold=True, before=0))
    D.add(7, out)
    # 29: formula card no longer overlaps the text
    for el in list(D.sptree(29)):
        nv = el.find('.//' + P + 'cNvPr')
        if nv is not None and (nv.get('name') or '') in ('Formula Card', 'Label', 'Line') and box(el) and box(el)[1] < 3.2:
            D.sptree(29).remove(el)
    ids = D.ids(29)
    for sp in D.sptree(29).iter(P + 'sp'):
        if 'הערכה מבוססת' in text(sp):
            xf = sp.find(P + 'spPr/' + A + 'xfrm')
            o_, e_ = xf.find(A + 'off'), xf.find(A + 'ext')
            right = int(o_.get('x')) + int(e_.get('cx'))
            o_.set('x', str(emu(5.1)))
            e_.set('cx', str(right - emu(5.1)))
    fx, fy = 0.55, 1.35
    D.add(29, [sp_xml(ids, 'Formula Card', fx, fy, 4.3, 1.55, 'roundRect', fill=TINT, adj={'adj': 12000}),
               label(ids, fx + 0.1, fy + 0.48, 1.25, 0.6, 'E(n) =', 18, NAVY, True),
               label(ids, fx + 1.3, fy + 0.1, 2.9, 0.55, '3 · A(n−1) + A(n−2)', 17, NAVY, True),
               line_xml(ids, fx + 1.4, fy + 0.77, fx + 4.1, fy + 0.77, NAVY, 2),
               label(ids, fx + 1.3, fy + 0.87, 2.9, 0.55, '4', 17, NAVY, True)])
    # 61: clean alignment
    ms = models(61)
    rebuild(61, ms, ['timeline', 'accordion', 'plain'])
    # 74: readable label on the dark podium
    for sp in D.sptree(74).iter(P + 'sp'):
        sppr = sp.find(P + 'spPr')
        f = sppr.find(A + 'solidFill') if sppr is not None else None
        if f is not None and f.find(A + 'srgbClr') is not None and lum(f.find(A + 'srgbClr').get('val')) < 0.35:
            for r in sp.iter(A + 'rPr'):
                for sf in r.findall(A + 'solidFill'):
                    r.remove(sf)
                r.insert(0, etree.fromstring(f'<a:solidFill xmlns:a="{NSA}"><a:srgbClr val="FFFFFF"/></a:solidFill>'))
    # 82: metrics as native cards (was an overflowing SmartArt)
    tree_ = smartart_tree(82)
    extra = [m for m in models(82, kinds=('textplain', 'boxed', 'shapetext'))]
    D.clear(82, KEEP + ('Section Number',))
    ids = D.ids(82)
    n = len(tree_)
    pos = ns['card_grid'](ids, n, Y0 + 0.05, Y1, 4)
    out = []
    for k, ((head, kids), (x, y, w, h)) in enumerate(zip(tree_, pos)):
        col = [NAVY, TEAL_D, ORANGE][k % 3]
        out.append(sp_xml(ids, f'Metric Card {k + 1}', x, y, w, h, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 6000}, shadow=True))
        out.append(sp_xml(ids, f'Metric Head {k + 1}', x, y, w, 0.6, 'round2SameRect', fill=col, adj={'adj1': 20000, 'adj2': 0}, anchor='ctr',
                          body=simple_para(head, 18, 'FFFFFF', True, 'ctr', True)))
        kid_ms = kids if kids else []
        if head.strip() == 'עלות' and extra:
            body = ''.join(ns['para_xml'](m, 14, BODY, 'sq', TEAL, indent=0.02, before=3 if j else 0) for j, m in enumerate(extra))
        else:
            body = ''.join(ns['para_xml']({'runs': [{'el': etree.fromstring(f'<a:r xmlns:a="{NSA}"><a:t>{esc(kk)}</a:t></a:r>'), 'text': kk, 'b': False,
                                                     'sz': 14, 'em': False, 'hl': False}], 'text': kk, 'rtl': True}, 14, BODY, 'sq', TEAL, indent=0.02,
                                          before=3 if j else 0) for j, kk in enumerate(kid_ms))
        out.append(sp_xml(ids, f'Metric Items {k + 1}', x + 0.1, y + 0.7, w - 0.2, h - 0.8, anchor='t', txbox=True, body=body,
                          ins=(0.08, 0.04, 0.12, 0.04)))
    D.add(82, out)


def smartart_tree(i):
    t = D.stree(i)
    rel = D.src.read('ppt/' + D.src_slides[i - 1].replace('slides/', 'slides/_rels/') + '.rels').decode()
    dm = re.findall(r'Target="\.\./(diagrams/data\d+\.xml)"', rel)[0]
    dt = etree.fromstring(D.src.read('ppt/' + dm))
    DG = '{http://schemas.openxmlformats.org/drawingml/2006/diagram}'
    pts = {}
    for p_ in dt.iter(DG + 'pt'):
        if p_.get('type', 'node') in ('node', 'doc'):
            pts[p_.get('modelId')] = (p_.get('type', 'node'), ' '.join(x.text or '' for x in p_.iter(A + 't')).strip())
    ch = {}
    for c in dt.iter(DG + 'cxn'):
        if c.get('type', 'parOf') == 'parOf':
            ch.setdefault(c.get('srcId'), []).append((int(c.get('srcOrd', '0')), c.get('destId')))
    doc = [k for k, v in pts.items() if v[0] == 'doc'][0]
    out = []
    for _, c in sorted(ch.get(doc, [])):
        if c in pts:
            out.append((pts[c][1], [pts[g][1] for _, g in sorted(ch.get(c, [])) if g in pts and pts[g][1]]))
    return out


def lum(c):
    r, g, b = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# =====================================================================
def tools_slide(i):
    """ch6 notebook card slides -> clean two-card layout"""
    t = D.stree(i)
    cls, tel, nel, rest = classify(t)
    X0, X1, Y0, Y1 = ns['X0'], ns['X1'], ns['Y0'], ns['Y1']
    sub, intro, note, cards = [], [], [], {'R': {'num': '', 'head': [], 'body': [], 'pic': None}, 'L': {'num': '', 'head': [], 'body': [], 'pic': None}}
    flat = []
    for k, e in rest:
        if k == 'grp':
            for c in e.iter(P + 'sp', P + 'pic'):
                flat.append(c)
        else:
            flat.append(e)
    # absolute boxes for grouped children: approximate via group transform
    def abs_box(el):
        b = box(el)
        if b is None:
            return None
        p = el.getparent()
        x, y, w, h = b
        while p is not None and etree.QName(p).localname == 'grpSp':
            xf = p.find(P + 'grpSpPr/' + A + 'xfrm')
            if xf is not None and xf.find(A + 'chOff') is not None:
                o, ex, co, ce = [xf.find(A + q) for q in ('off', 'ext', 'chOff', 'chExt')]
                sx = int(ex.get('cx')) / max(1, int(ce.get('cx')))
                sy = int(ex.get('cy')) / max(1, int(ce.get('cy')))
                x = int(o.get('x')) / E + (x - int(co.get('x')) / E) * sx
                y = int(o.get('y')) / E + (y - int(co.get('y')) / E) * sy
                w, h = w * sx, h * sy
            p = p.getparent()
        return [x, y, w, h]
    for el in flat:
        nm = el.find('.//' + P + 'cNvPr').get('name') or ''
        b = abs_box(el)
        if b is None:
            continue
        side = 'R' if b[0] + b[2] / 2 > D.W / 2 else 'L'
        tag = etree.QName(el).localname
        if tag == 'pic':
            if cards[side]['pic'] is None:
                cards[side]['pic'] = el
            continue
        tx = text(el).strip()
        if not tx:
            continue
        ps = [m for m in ns['extract_paras']([el]) if m]
        if nm.startswith('Subtitle'):
            sub += ps
        elif re.match(r'^0\d$', tx):
            cards[side]['num'] = tx
        elif b[1] < 2.2:
            intro += ps
        elif b[1] > 6.1 and b[2] > 6:
            note += ps
        elif nm.startswith('Rectangle 27') and not cards[side]['head']:
            cards[side]['head'] = ps
        else:
            cards[side]['body'] += ps
    hs = {s: ' '.join(m['text'] for m in cards[s]['head']).strip() for s in ('R', 'L')}
    if any(h.endswith(':') for h in hs.values()) and all(cards[s]['body'] for s in ('R', 'L')):
        cards['R']['body'], cards['L']['body'] = cards['L']['body'], cards['R']['body']
    # a lead-in line such as 'כלים אלו מאפשרים:' belongs with the list it introduces
    for s in ('R', 'L'):
        lead = [m for m in cards[s]['body'] if m['text'].strip().endswith(':') and len(m['text']) < 40]
        if lead:
            o_ = 'L' if s == 'R' else 'R'
            if len(cards[o_]['body']) > len(cards[s]['body']):
                for m in lead:
                    cards[s]['body'].remove(m)
                cards[o_]['body'] = lead + cards[o_]['body']
    D.clear(i)
    ids = D.ids(i)
    out = []
    y = Y0 - 0.05
    hdr = sub[:1]
    rest_intro = sub[1:] + intro
    if hdr:
        out.append(rich_box(ids, 'Subtitle', X0, y, X1 - X0, 0.45, hdr, 18, OR_D, anchor='ctr', bold=True))
        y += 0.45
    if rest_intro:
        h = 0.32 * len(rest_intro) + 0.25
        pt = fitpt(rest_intro, X1 - X0, h, 14, 10)
        out.append(rich_box(ids, 'Intro', X0, y, X1 - X0, h, rest_intro, pt, BODY, anchor='t'))
        y += h + 0.05
    bottom = Y1
    if note:
        nh = 0.7
        out.append(rich_box(ids, 'Note', X0, Y1 - nh, X1 - X0, nh, note, 13, 'FFFFFF', algn='ctr', anchor='ctr', fill=NAVY, geom='roundRect', bold=True,
                            ins=(0.2, 0.05, 0.2, 0.05)))
        bottom = Y1 - nh - 0.15
    used = [s for s in ('R', 'L') if cards[s]['head'] or cards[s]['body']]
    n = len(used)
    gap = 0.3
    cw = (X1 - X0 - gap * (n - 1)) / n if n > 1 else min(6.0, X1 - X0)
    for k, s in enumerate(used):
        c = cards[s]
        x = X1 - (k + 1) * cw - k * gap if n > 1 else (X0 + X1 - cw) / 2
        ch = bottom - y - 0.05
        out.append(sp_xml(ids, f'Tool Card {k + 1}', x, y + 0.05, cw, ch, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 5000}, shadow=True))
        out.append(sp_xml(ids, f'Tool Bar {k + 1}', x, y + 0.05, cw, 0.1, 'rect', fill=[TEAL, ORANGE][k % 2]))
        iy = y + 0.25
        ih = min(1.45, ch * 0.3)
        if c['pic'] is not None:
            out.append(D.copy_src_pic(i, c['pic'], x + 0.2, iy, cw - 0.4, ih))
        yy = iy + ih + 0.1
        if c['num']:
            out.append(sp_xml(ids, f'Tool Num {k + 1}', x + cw - 0.68, yy, 0.5, 0.5, 'ellipse', fill=NAVY, anchor='ctr', ins=(0, 0, 0, 0),
                              body=simple_para(c['num'], 13, 'FFFFFF', True, 'ctr', False)))
        if c['head']:
            hh = 0.62
            out.append(rich_box(ids, f'Tool Title {k + 1}', x + 0.15, yy, cw - 0.9, hh, c['head'], fitpt(c['head'], cw - 0.9, hh, 15, 10), NAVY,
                                anchor='ctr', bold=True))
            yy += hh + 0.08
        if c['body']:
            bh = y + 0.05 + ch - yy - 0.15
            pt = fitpt(c['body'], cw - 0.35, bh, 14, 8.5, 0.25)
            out.append(rich_box(ids, f'Tool Text {k + 1}', x + 0.15, yy, cw - 0.3, bh, c['body'], pt, BODY, anchor='t', before=3))
    D.add(i, out)


def deck6():
    for i in range(9, 18):
        tools_slide(i)
    tools_slide(19)


{1: deck1, 2: deck2, 3: deck3, 4: deck4, 5: deck5, 6: deck6}[N]()
out = sys.argv[3]
D.save(out)
if D.deleted:
    # drop orphaned parts
    S = '/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx/scripts'
    tmp = '/tmp/clean_' + str(N)
    shutil.rmtree(tmp, ignore_errors=True)
    import zipfile
    zipfile.ZipFile(out).extractall(tmp)
    subprocess.run(['python3', S + '/clean.py', tmp], check=True, capture_output=True)
    os.remove(out)
    subprocess.run(f'cd {tmp} && zip -qXrDy {os.path.abspath(out)} .', shell=True, check=True)
print('patched', N, 'deleted', D.deleted)
