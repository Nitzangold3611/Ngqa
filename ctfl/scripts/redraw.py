# native redraws of content images, keyed by "deck-slide-pic"; each fn(ids, x, y, w, h) -> [xml]
import math
from lay import *

REG = {}


def reg(*labels):
    def d(f):
        for l in labels:
            REG[l] = f
        return f
    return d


def get(label):
    return REG.get(label)


def box_t(ids, name, x, y, w, h, txt, fill=NAVY, color='FFFFFF', pt=14, geom='roundRect', bold=True, line=None, adj=None):
    body = ''.join(simple_para(t, pt, color, bold, 'ctr') for t in txt.split('\n'))
    return sp_xml(ids, name, x, y, w, h, geom, fill=fill, line=line, anchor='ctr', ins=(0.05, 0.03, 0.05, 0.03), body=body,
                  adj=adj or ({'adj': 18000} if geom == 'roundRect' else None))


def label(ids, x, y, w, h, txt, pt=12, color=BODY, bold=False, algn='ctr'):
    body = ''.join(simple_para(t, pt, color, bold, algn) for t in txt.split('\n'))
    return sp_xml(ids, 'Label', x, y, w, h, anchor='ctr', ins=(0.02, 0, 0.02, 0), body=body, txbox=True)


def arrow(ids, x1, y1, x2, y2, color=GRAY, lw=2.0):
    return line_xml(ids, x1, y1, x2, y2, color, lw, tail='triangle')


def fit_pt(texts, w, h, mx=16, mn=8, bold=True):
    pt = mx
    while pt > mn:
        if all(para_lines([(t, bold, 1)], w * 0.9, pt) * pt * 1.2 / 72 <= h * 0.9 for t in texts):
            return pt
        pt -= 0.5
    return mn


def square(x, y, w, h, ratio=1.0):
    if w / h > ratio:
        nw = h * ratio
        return x + (w - nw) / 2, y, nw, h
    nh = w / ratio
    return x, y + (h - nh) / 2, w, nh


def cycle(ids, x, y, w, h, items, center=None, colors=(NAVY, TEAL_D, ORANGE)):
    x, y, w, h = square(x, y, w, h, 1.25)
    cx, cy = x + w / 2, y + h / 2
    n = len(items)
    rx, ry = w / 2 - w * 0.17, h / 2 - h * 0.16
    bw, bh = min(w * 0.32, 2.4), min(h * 0.24, 1.0)
    pt = fit_pt(items, bw - 0.1, bh - 0.05, 14, 8)
    out = [sp_xml(ids, 'Cycle Ring', cx - rx, cy - ry, 2 * rx, 2 * ry, 'ellipse', line=TINT, lw=10)]
    for k in range(n):
        a = -math.pi / 2 - 2 * math.pi * k / n  # counter-clockwise visually = RTL reading
        a = -math.pi / 2 + 2 * math.pi * k / n
        px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
        # arrow head marker between nodes
        a2 = a + math.pi / n
        ax, ay = cx + rx * math.cos(a2), cy + ry * math.sin(a2)
        out.append(sp_xml(ids, 'Cycle Arrow', ax - 0.14, ay - 0.14, 0.28, 0.28, 'triangle', fill=ORANGE,
                          rot=math.degrees(a2) + 180))
    for k, t in enumerate(items):
        a = -math.pi / 2 + 2 * math.pi * k / n
        px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
        out.append(box_t(ids, f'Cycle Step {k + 1}', px - bw / 2, py - bh / 2, bw, bh, t, colors[k % len(colors)], pt=pt))
    if center:
        cs = min(w, h) * 0.3
        out.append(box_t(ids, 'Cycle Center', cx - cs / 2, cy - cs / 2, cs, cs, center, TINT, NAVY, fit_pt([center], cs, cs, 18, 9), 'ellipse'))
    return out


def chain(ids, x, y, w, h, items, vertical=False, rtl=True, colors=(NAVY, TEAL_D, ORANGE)):
    n = len(items)
    out = []
    gap = 0.35
    if vertical:
        bh = min(0.9, (h - gap * (n - 1)) / n)
        bw = min(w, 4.5)
        y0 = y + (h - (bh * n + gap * (n - 1))) / 2
        bx = x + (w - bw) / 2
        pt = fit_pt(items, bw, bh, 16, 8)
        for k, t in enumerate(items):
            yy = y0 + k * (bh + gap)
            out.append(box_t(ids, f'Step {k + 1}', bx, yy, bw, bh, t, colors[k % len(colors)], pt=pt))
            if k < n - 1:
                out.append(arrow(ids, bx + bw / 2, yy + bh + 0.03, bx + bw / 2, yy + bh + gap - 0.03, ORANGE, 2.5))
    else:
        bw = (w - gap * (n - 1)) / n
        bh = min(h, max(0.8, bw * 0.6))
        y0 = y + (h - bh) / 2
        pt = fit_pt(items, bw, bh, 16, 8)
        for k, t in enumerate(items):
            i = n - 1 - k if rtl else k
            xx = x + i * (bw + gap)
            out.append(box_t(ids, f'Step {k + 1}', xx, y0, bw, bh, t, colors[k % len(colors)], pt=pt))
            if k < n - 1:
                if rtl:
                    out.append(arrow(ids, xx - 0.03, y0 + bh / 2, xx - gap + 0.03, y0 + bh / 2, ORANGE, 2.5))
                else:
                    out.append(arrow(ids, xx + bw + 0.03, y0 + bh / 2, xx + bw + gap - 0.03, y0 + bh / 2, ORANGE, 2.5))
    return out


def table(ids, x, y, w, h, rows, colw=None, pt=None):
    nr, nc = len(rows), len(rows[0])
    colw = colw or [1] * nc
    s = sum(colw)
    cws = [w * c / s for c in colw]
    rh = min(0.6, h / nr)
    y0 = y + (h - rh * nr) / 2
    if pt is None:
        pt = min(fit_pt([str(c) for r in rows for c in r], min(cws), rh, 16, 8, False), 16)
    out = []
    for r, row in enumerate(rows):
        xx = x + w
        for c, val in enumerate(row):
            xx -= cws[c]  # RTL columns? keep given order right->left
        xx = x
        for c, val in enumerate(row):
            fill = NAVY if r == 0 else (SOFT if r % 2 == 0 else 'FFFFFF')
            col = 'FFFFFF' if r == 0 else BODY
            out.append(box_t(ids, f'Cell {r}-{c}', xx, y0 + r * rh, cws[c], rh, str(val), fill, col, pt, 'rect', bold=(r == 0 or c == 0),
                             line=LINE))
            xx += cws[c]
    return out


# ---------------- figures ----------------
@reg('1-84-0')
def f_indep(ids, x, y, w, h):
    items = ['אין עצמאות של הבדיקות - המפתח בודק את הקוד שהוא כתב', 'עצמאות נמוכה מפתח אחר מצוות הפיתוח בודק את הקוד',
             'עצמאות גבוהה צוות בדיקות עצמאי מחוץ לפיתוח אך בתוך הארגון', 'עצמאות גבוהה מאוד בודקים חיצוניים לארגון']
    n = 4
    out = []
    sh = (h - 0.3) / n
    pt = fit_pt(items, w - 1.4, sh - 0.1, 15, 9, True)
    cols = [NAVY, TEAL_D, TEAL, ORANGE]
    for k, t in enumerate(items):
        yy = y + k * (sh + 0.1)
        ind = k * (w * 0.06)
        bw = w - w * 0.18
        bx = x + w - bw - ind
        out.append(sp_xml(ids, f'Level {k + 1}', bx, yy, bw, sh, 'roundRect', fill=cols[k], adj={'adj': 30000}, anchor='ctr',
                          ins=(0.15, 0.03, 0.85, 0.03), body=simple_para(t, pt, 'FFFFFF' if k != 2 else NAVY, True, 'r', True)))
        out.append(sp_xml(ids, f'Level Num {k + 1}', bx + bw - 0.72, yy + (sh - 0.56) / 2, 0.56, 0.56, 'ellipse', fill='FFFFFF', anchor='ctr',
                          ins=(0, 0, 0, 0), body=simple_para(f'{k + 1:02d}', 14, cols[k] if k != 2 else TEAL_D, True, 'ctr', False)))
    return out


@reg('5-26-0')
def f_effort(ids, x, y, w, h):
    rows = [['Project', 'Development effort ($)', 'Test effort ($)'], ['P1', '800,000', '40,000'], ['P2', '1,200,000', '130,000'],
            ['P3', '600,000', '70,000'], ['P4', '1,000,000', '120,000']]
    return table(ids, x, y, w, min(h, 3.2), rows, [1, 2, 1.6])


@reg('3-8-0')
def f_cost(ids, x, y, w, h):
    data = [('Rqmnts.', 139, '$139'), ('Design', 455, '$455'), ('Coding', 977, '$977'), ('Testing', 7136, '$7,136'), ('Maint.', 14102, '$14,102')]
    out = [label(ids, x, y, w, 0.45, "It's all about Fixing it sooner", 16, NAVY, True)]
    top, bot = y + 0.8, y + h - 0.75
    n = len(data)
    bw = w / n * 0.6
    mx = 14102
    for k, (l, v, s) in enumerate(data):
        bx = x + k * w / n + (w / n - bw) / 2
        bh = max(0.06, (bot - top - 0.35) * v / mx)
        out.append(sp_xml(ids, f'Bar {l}', bx, bot - bh, bw, bh, 'rect', fill=ORANGE if k >= 3 else TEAL_D))
        out.append(label(ids, bx - 0.3, bot - bh - 0.35, bw + 0.6, 0.32, s, 12, NAVY, True))
        out.append(label(ids, bx - 0.3, bot + 0.05, bw + 0.6, 0.3, l, 11, BODY))
    out.append(line_xml(ids, x, bot, x + w, bot, GRAY, 1))
    out.append(label(ids, x, bot + 0.38, w, 0.3, 'Software Development Lifecycle Phase', 10, GRAY))
    return out


@reg('2-11-0')
def f_waterfall(ids, x, y, w, h):
    items = ['דרישות', 'תכנון', 'מימוש', 'בדיקות', 'תחזוקה']
    n = len(items)
    out = []
    bw, bh = w * 0.34, min(0.7, h / n * 0.7)
    step = (h - bh) / (n - 1)
    sx = (w - bw) / (n - 1)
    cols = [NAVY, TEAL_D, TEAL, ORANGE, NAVY]
    for k, t in enumerate(items):
        bx, by = x + w - bw - k * sx, y + k * step
        out.append(box_t(ids, f'Phase {k + 1}', bx, by, bw, bh, t, cols[k], 'FFFFFF' if k != 2 else NAVY, 16))
        if k < n - 1:
            out.append(line_xml(ids, bx + bw * 0.25, by + bh, bx + bw * 0.25, by + step + bh / 2, ORANGE, 2.25))
            out.append(arrow(ids, bx + bw * 0.25, by + step + bh / 2, bx - sx + bw + 0.02, by + step + bh / 2, ORANGE, 2.25))
    return out


@reg('2-15-0', '3-4-0')
def f_vmodel(ids, x, y, w, h):
    L = ['Business Requirements', 'High-Level Design', 'Low-Level Design']
    Rr = ['Acceptance Tests', 'System Tests', 'Integration Tests']
    out = []
    bw, bh = min(2.4, w * 0.3), 0.55
    rows = 4
    top = y + 0.1
    step = (h - 0.9 - bh) / (rows - 1)
    for k in range(3):
        by = top + k * step
        lx = x + k * (w * 0.1)
        rx = x + w - bw - k * (w * 0.1)
        out.append(box_t(ids, f'V Left {k + 1}', lx, by, bw, bh, L[k], NAVY, pt=13))
        out.append(box_t(ids, f'V Right {k + 1}', rx, by, bw, bh, Rr[k], TEAL_D, pt=13))
        out.append(line_xml(ids, rx - 0.05, by + bh / 2, lx + bw + 0.05, by + bh / 2, ORANGE, 1.5, tail='triangle', dash='dash'))
        if k < 2:
            out.append(arrow(ids, lx + bw / 2, by + bh + 0.02, lx + w * 0.1 + bw / 2, by + step - 0.02, GRAY, 2))
            out.append(arrow(ids, rx + bw / 2, by + step - 0.02, rx + bw / 2 - 0.0 + 0, by + bh + 0.02, GRAY, 2))
    cy = top + 3 * step
    cw = w * 0.36
    out.append(box_t(ids, 'V Code', x + (w - cw) / 2, cy, cw, bh, 'Code   ⇄   Unit Tests', ORANGE, pt=13))
    out.append(arrow(ids, x + 0.2 * w + bw / 2, top + 2 * step + bh + 0.02, x + (w - cw) / 2 + 0.3, cy + 0.1, GRAY, 2))
    out.append(arrow(ids, x + (w + cw) / 2 - 0.3, cy + 0.1, x + w - 0.2 * w - bw / 2, top + 2 * step + bh + 0.02, GRAY, 2))
    out.append(label(ids, x, y + h - 0.45, w, 0.4, 'V-Model : Development & Testing', 14, NAVY, True))
    return out


@reg('2-64-0')
def f_values(ids, x, y, w, h):
    return cycle(ids, x, y, w, h, ['Individuals and interactions over processes and tools',
                                   'Working software over comprehensive documentation',
                                   'Customer collaboration over contract negotiation',
                                   'Responding to change over following a plan'], 'Agile\nValues')


@reg('2-99-0')
def f_ci(ids, x, y, w, h):
    out = chain(ids, x, y, w, h * 0.7, ['Commit', 'Build', 'Test', 'Stage', 'Deploy Dev/QA'], rtl=False)
    out.append(sp_xml(ids, 'CI Bar', x, y + h * 0.72, w, 0.5, 'leftRightArrow', fill=TINT, anchor='ctr',
                      body=simple_para('Continuous Integration/Delivery', 13, NAVY, True, 'ctr', False)))
    return out


@reg('4-96-0')
def f_atdd(ids, x, y, w, h):
    return cycle(ids, x, y, w, h, ['discuss\nin workshop', 'develop\nin concurrence', 'deliver\nfor acceptance'])


@reg('4-98-0')
def f_atdd2(ids, x, y, w, h):
    return cycle(ids, x, y, w, h, ['Specify', 'Develop', 'Deliver'], 'ATDD')


@reg('5-27-0', '5-29-0')
def f_formula(ids, x, y, w, h):
    cy = y + h / 2
    fx = x + w * 0.38
    fw = w * 0.55
    return [sp_xml(ids, 'Formula Card', x + 0.1, cy - 0.85, w - 0.2, 1.7, 'roundRect', fill=TINT, adj={'adj': 12000}),
            label(ids, x + 0.2, cy - 0.3, w * 0.18 + 0.4, 0.6, 'E(n) =', 24, NAVY, True),
            label(ids, fx - 0.2, cy - 0.72, fw, 0.6, '3 · A(n−1) + A(n−2)', 24, NAVY, True),
            line_xml(ids, fx - 0.1, cy, fx + fw - 0.3, cy, NAVY, 2),
            label(ids, fx - 0.2, cy + 0.1, fw, 0.6, '4', 24, NAVY, True)]


@reg('5-68-0')
def f_riskresp(ids, x, y, w, h):
    x, y, w, h = square(x, y, w, h, 1.3)
    cx, cy = x + w / 2, y + h / 2
    out = [box_t(ids, 'Risk', cx - 0.8, cy - 0.4, 1.6, 0.8, 'RISK', ORANGE, pt=22)]
    bw, bh = w * 0.34, 0.65
    for k, (t, px, py) in enumerate([('REDUCE', x, y), ('TRANSFER', x + w - bw, y), ('ACCEPT', x, y + h - bh), ('AVOID', x + w - bw, y + h - bh)]):
        out.append(box_t(ids, t, px, py, bw, bh, t, [NAVY, TEAL_D, TEAL_D, NAVY][k], pt=16))
        tx = px + bw / 2
        ty = py + (bh if py == y else 0)
        out.append(line_xml(ids, cx + (-0.5 if px == x else 0.5), cy + (-0.4 if py == y else 0.4), tx, ty, GRAY, 2, tail='triangle'))
    return out


@reg('5-70-0')
def f_change(ids, x, y, w, h):
    return cycle(ids, x, y, w, h, ['What do we have?', 'What are the risks?', "What's changing?"], 'Risk-Based\nTesting')


@reg('5-113-0')
def f_defect(ids, x, y, w, h):
    return cycle(ids, x, y, w, h, ['Discovery', 'Categorization', 'Resolution', 'Verification', 'Closure', 'Reporting'])


@reg()
def f_tdd(ids, x, y, w, h):
    return cycle(ids, x, y, w, h, ['Write Failing Test', 'Make Test Pass', 'Refactor'], 'TDD')


@reg()
def f_devops(ids, x, y, w, h):
    return cycle(ids, x, y, w, h, ['PLAN', 'CODE', 'BUILD', 'TEST', 'RELEASE', 'DEPLOY', 'OPERATE', 'MEASURE'], 'DevOps')


@reg('2-40-0')
def f_story(ids, x, y, w, h):
    x, y, w, h = square(x, y, w, h, 1.6)
    body = ''.join(simple_para(t, 22, NAVY, False, 'l', False) for t in ['As a <user role>', 'I want <goal>', 'so that <benefit>.'])
    return [sp_xml(ids, 'Story Card', x, y, w, h, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 6000}, shadow=True, anchor='ctr',
                   ins=(0.5, 0.2, 0.3, 0.2), body=body),
            sp_xml(ids, 'Story Edge', x, y, 0.14, h, 'rect', fill=TEAL)]
