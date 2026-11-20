import re
#!/usr/bin/env python3
"""CT-GenAI decks in the NGQA/CTFL v2 style, built from JSON specs.
usage: gbuild.py N spec.jsonl out.pptx"""
import sys, os, re, json, zipfile, shutil, tempfile, math
sys.path.insert(0, '/home/claude/work')
from lay import (sp_xml, pic_xml, line_xml, wlen, fit_size, esc, emu, solid, Ids, HEB,
                 NAVY, TEAL, TEAL_D, ORANGE, BODY, GRAY, TINT, LINE, SOFT, OR_D, EMPH)

N = int(sys.argv[1]); SPEC = sys.argv[2]; DST = sys.argv[3]
TPL = '/home/claude/work/final_1.pptx'
ICONS = '/home/claude/genai/icons'
CHAPTER = {1: 'מבוא לבינה מלאכותית יוצרת בבדיקות תוכנה', 2: 'הנדסת פרומפטים לבדיקות תוכנה',
           3: 'ניהול סיכונים ב-GenAI', 4: 'LLMOps ותשתיות GenAI', 5: 'הטמעת GenAI בארגון'}
CH_OVR = json.load(open('/home/claude/genai/chapters.json')) if os.path.exists('/home/claude/genai/chapters.json') else {}
if str(N) in CH_OVR:
    CHAPTER[N] = CH_OVR[str(N)]

W, H = 13.333, 7.5
X0, X1 = 0.55, 12.8
TX0 = 1.95
TITLE_Y = 0.24
FOOT = 6.86
ACC = [TEAL, ORANGE, NAVY]
GOOD, BAD = '12A37A', 'E0475B'
MONO = 'Consolas'


def heb(s):
    return bool(HEB.search(s or ''))


# ---------------------------------------------------------------- text
def run(t, pt, col, b=False, font='Arial', i=False):
    lang = 'he-IL' if heb(t) else 'en-US'
    bb = ' b="1"' if b else ''
    ii = ' i="1"' if i else ''
    sp = ' xml:space="preserve"' if t != t.strip() else ''
    return (f'<a:r><a:rPr lang="{lang}" sz="{int(round(pt * 2)) * 50}"{bb}{ii} dirty="0">{solid(col)}'
            f'<a:latin typeface="{font}"/><a:cs typeface="{font}"/></a:rPr><a:t{sp}>{esc(t)}</a:t></a:r>')


def runs_md(t, pt, col, b=False, font='Arial', bcol=None):
    """**bold** segments"""
    out = []
    for k, seg in enumerate(re.split(r'\*\*', t)):
        if not seg:
            continue
        bold = b or (k % 2 == 1)
        out.append(run(seg, pt, (bcol or col) if (k % 2 == 1) else col, bold, font))
    return ''.join(out)


def P(t, pt, col=BODY, b=False, al=None, bullet=None, bcol=TEAL, before=0, font='Arial', rtl=None, line=None, i=False):
    if rtl is None:
        rtl = heb(t) or al == 'r'
    if al is None:
        al = 'r'
    bu = '<a:buNone/>'
    mar = ''
    if bullet:
        ch = {'sq': '■', 'dot': '●', 'check': '✓', 'x': '✗', 'dash': '–', 'arrow': '◂'}.get(bullet, bullet)
        bsz = 70 if bullet in ('sq', 'dot') else 100
        bu = f'<a:buClr><a:srgbClr val="{bcol}"/></a:buClr><a:buSzPct val="{bsz * 1000}"/><a:buFont typeface="Arial"/><a:buChar char="{ch}"/>'
        ind = 0.24 * pt / 16
        mar = f' marL="{emu(ind)}" indent="{-emu(ind)}"'
    ln = f'<a:lnSpc><a:spcPct val="{int((line or 1.0) * 100000)}"/></a:lnSpc>'
    sb = f'<a:spcBef><a:spcPts val="{int(before * 100)}"/></a:spcBef>'
    body = runs_md(t, pt, col, b, font, bcol=EMPH if col in (BODY, NAVY) else None) if '**' in t else run(t, pt, col, b, font, i)
    return (f'<a:p><a:pPr{mar} algn="{al}" rtl="{1 if rtl else 0}">{ln}{sb}{bu}</a:pPr>{body}'
            f'<a:endParaRPr lang="he-IL" sz="{int(pt * 100)}"/></a:p>')


# kinds: h head, s sub (teal), x body, b bullet, g gray small, c code, t big title, n number
KREL = {'h': 1.12, 's': 0.86, 'x': 1.0, 'b': 1.0, 'g': 0.8, 'c': 0.88, 't': 1.35, 'n': 1.6, 'o': 0.86, 'k': 1.0, 'v': 1.0}
KBOLD = {'h': True, 't': True, 'n': True, 'o': True, 'k': True}


def meas(items):
    out = []
    for t, k in items:
        out.append({'mruns': [(t.replace('**', ''), KBOLD.get(k, False), 1.0)], 'rel': KREL.get(k, 1.0),
                    'indent': 0.2 if k in ('b', 'k', 'v') else 0, 'sp': 0.55 if k in ('s', 'g') else 1.0})
    return out


def fit(items, w, h, maxpt, minpt, spacing=0.42):
    pt = fit_size(meas(items), w * 0.96, h, maxpt, minpt, spacing)
    return pt


def paras(items, pt, al='r', col=BODY, hcol=NAVY, spacing=0.42, bcol=TEAL):
    out = []
    for k, (t, kd) in enumerate(items):
        rel = KREL.get(kd, 1.0)
        bef = 0 if k == 0 else pt * spacing * (0.55 if kd in ('s', 'g') else 1.0)
        if kd == 'h':
            out.append(P(t, pt * rel, hcol, True, al, before=bef))
        elif kd == 't':
            out.append(P(t, pt * rel, hcol, True, al, before=bef))
        elif kd == 'n':
            out.append(P(t, pt * rel, TEAL_D, True, al, before=bef))
        elif kd == 's':
            out.append(P(t, pt * rel, TEAL_D, False, al, before=bef))
        elif kd == 'o':
            out.append(P(t, pt * rel, OR_D, True, al, before=bef))
        elif kd == 'g':
            out.append(P(t, pt * rel, GRAY, False, al, before=bef))
        elif kd == 'b':
            out.append(P(t, pt * rel, col, False, 'r', bullet='sq', bcol=bcol, before=bef))
        elif kd == 'k':
            out.append(P(t, pt * rel, col, False, 'r', bullet='check', bcol=GOOD, before=bef))
        elif kd == 'v':
            out.append(P(t, pt * rel, col, False, 'r', bullet='x', bcol=BAD, before=bef))
        elif kd == 'c':
            out.append(P(t, pt * rel, col, False, 'l', before=bef, font=MONO, rtl=heb(t)))
        else:
            out.append(P(t, pt * rel, col, False, al, before=bef))
    return ''.join(out)


class Slide:
    def __init__(self, layout=2):
        self.ids = Ids(10)
        self.xml = []
        self.rels = []  # (rid, type, target)
        self.layout = layout
        self.links = []  # site link boxes
        self.dark = False

    def add(self, x):
        self.xml.append(x)

    def media(self, path):
        for rid, ty, tg in self.rels:
            if tg.endswith('/' + os.path.basename(path)):
                return rid
        rid = f'rId{len(self.rels) + 10}'
        MEDIA[os.path.basename(path)] = path
        self.rels.append((rid, 'image', '../media/g_' + os.path.basename(path)))
        return rid

    def icon(self, key, x, y, s, var='t'):
        p = f'{ICONS}/{key}_{var}.png'
        if not key or not os.path.exists(p):
            return
        self.add(pic_xml(self.ids, self.media(p), x, y, s, s, name='Icon', descr=key))

    def box(self, name, x, y, w, h, items=None, maxpt=16, minpt=9, al='r', anchor='t', fill=None, line=None, lw=1.0,
            geom='roundRect', adj=None, ins=(0.12, 0.08, 0.12, 0.08), shadow=False, col=BODY, hcol=NAVY, spacing=0.42,
            pt=None, bcol=TEAL, dash=None):
        body = ''
        if items:
            iw = w - ins[0] - ins[2]
            ih = h - ins[1] - ins[3]
            if pt is None:
                mp = maxpt
                for t, k in items:
                    for wd in t.replace('**', '').split():
                        while mp > minpt and wlen(wd, mp * KREL.get(k, 1.0), KBOLD.get(k, False)) * 1.2 > iw:
                            mp -= 0.5
                pt = fit(items, iw, ih, mp, minpt, spacing) or minpt
            else:
                ew = iw * (0.7 if geom == 'ellipse' else 1.0)
                for t, k in items:
                    for wd in t.replace('**', '').split():
                        while pt > 8 and wlen(wd, pt * KREL.get(k, 1.0), KBOLD.get(k, False)) * 1.15 > ew:
                            pt -= 0.5
            self.last_pt = pt
            body = paras(items, pt, al, col, hcol, spacing, bcol)
        if geom == 'roundRect' and adj is None:
            adj = {'adj': int(min(16000, 0.12 / max(0.2, min(w, h)) * 100000))}
        self.add(sp_xml(self.ids, name, x, y, w, h, geom, fill=fill, line=line, lw=lw, adj=adj, body=body, anchor=anchor,
                        ins=ins, shadow=shadow, txbox=True, dash=dash))
        return pt

    def rect(self, x, y, w, h, fill, geom='rect', adj=None, line=None, lw=1, name='Shape', alpha=None, dash=None):
        self.add(sp_xml(self.ids, name, x, y, w, h, geom, fill=fill, line=line, lw=lw, adj=adj, alpha=alpha, dash=dash))

    def line(self, x1, y1, x2, y2, col=TEAL, lw=1.5, arrow=True, dash=None, head=False):
        self.add(line_xml(self.ids, x1, y1, x2, y2, col, lw, tail='triangle' if arrow else None,
                          head='triangle' if head else None, dash=dash))

    def text(self, t, x, y, w, h, pt, col=BODY, b=False, al='r', anchor='ctr', font='Arial', name='Text'):
        self.add(sp_xml(self.ids, name, x, y, w, h, 'rect', body=P(t, pt, col, b, al, font=font), anchor=anchor,
                        ins=(0.02, 0, 0.02, 0), txbox=True))


MEDIA = {}


# ---------------------------------------------------------------- common parts
def title(s, sp, dark=False):
    t = sp.get('t', '')
    k = sp.get('k', '')
    t2 = sp.get('t2')
    width = X1 - TX0
    pt = 28
    full = t
    while pt > 17 and wlen(full, pt, 1) * 1.04 > width - 0.1:
        pt -= 0.5
    ty = TITLE_Y
    if k:
        s.text(k, TX0, TITLE_Y - 0.12, width, 0.3, 12, TEAL_D, True, 'r', name='Kicker')
        ty = TITLE_Y + 0.12
        pt = min(pt, 26)
    s.add(sp_xml(s.ids, 'Title', TX0, ty, width, 0.62, anchor='ctr', ins=(0.02, 0, 0.02, 0), wrap=False, ph='title',
                 body=P(t, pt, 'FFFFFF' if dark else NAVY, True, 'r')))
    s.rect(X1 - 1.15, ty + 0.68, 1.15, 0.06, TEAL, name='Title Accent')
    s.rect(X1 - 1.42, ty + 0.68, 0.2, 0.06, ORANGE, name='Title Accent 2')
    top = ty + 0.86
    sub = sp.get('sub') or t2
    if sub:
        s.text(sub, X0 + 1.2, top - 0.04, X1 - X0 - 1.2, 0.34, 14 if t2 and not sp.get('sub') else 13,
               TEAL_D if (t2 and not sp.get('sub')) else GRAY, bool(t2 and not sp.get('sub')), 'r', name='Subtitle')
        top += 0.36
    return top + 0.1


def note(s, n, y=None, h=None):
    """exam / highlight bar at the bottom"""
    if not n:
        return 6.78
    y = y or 6.12
    h = h or (6.74 - y)
    lab = n.get('lab')
    tone = n.get('tone', 'warn' if lab and 'דגש' in lab else 'info')
    fill, bar, lc = ('FFF6EA', ORANGE, OR_D) if tone == 'warn' else ('EAFBFA', TEAL, TEAL_D)
    s.rect(X0, y, X1 - X0, h, fill, 'roundRect', {'adj': 18000}, name='Note')
    s.rect(X1 - 0.08, y, 0.08, h, bar, name='Note Bar')
    items = []
    txt = n.get('x', '')
    if n.get('h'):
        items.append((n['h'], 'h'))
    if lab:
        txt = f'**{lab}** {txt}' if txt else f'**{lab}**'
    items.append((txt, 'x'))
    if n.get('en'):
        items.append((n['en'], 'g'))
    iw = X1 - X0 - 0.5
    pt = fit(items, iw, h - 0.08, 15, 9.5) or 9.5
    body = ''.join(P(t.replace(f'**{lab}**', '') if False else t, pt * KREL[k], GRAY if k == 'g' else (NAVY if k == 'h' else BODY),
                     k == 'h', 'r', before=0 if j == 0 else 2) for j, (t, k) in enumerate(items))
    # colour the label
    if lab:
        body = body.replace(run(lab, pt, EMPH, True), run(lab, pt, lc, True))
    s.add(sp_xml(s.ids, 'Note Text', X0 + 0.2, y, iw, h, 'rect', body=body, anchor='ctr', ins=(0.05, 0.02, 0.05, 0.02), txbox=True))
    return y - 0.16


def cap(s, t, y):
    if t:
        s.text(t, X0, y, X1 - X0, 0.34, 12.5, GRAY, False, 'ctr', name='Caption')


def pills(s, labels, x, y, w, h=0.42, maxpt=13, fill=TINT, col=TEAL_D, line=None, gap=0.12, al='r'):
    """row of pills, right to left"""
    if not labels:
        return
    pt = maxpt
    while pt > 8:
        ws = [wlen(l, pt, 1) + 0.36 for l in labels]
        if sum(ws) + gap * (len(ws) - 1) <= w:
            break
        pt -= 0.5
    ws = [wlen(l, pt, 1) + 0.36 for l in labels]
    tot = sum(ws) + gap * (len(ws) - 1)
    if tot > w:  # two rows
        half = (len(labels) + 1) // 2
        pills(s, labels[:half], x, y, w, h * 0.9, maxpt, fill, col, line, gap, al)
        pills(s, labels[half:], x, y + h + 0.1, w, h * 0.9, maxpt, fill, col, line, gap, al)
        return
    cx = x + w if al == 'r' else x + (w + tot) / 2
    for l, ww in zip(labels, ws):
        s.box('Pill', cx - ww, y, ww, h, [(l, 'k')], pt=pt, al='ctr', anchor='ctr', fill=fill, line=line,
              adj={'adj': 50000}, ins=(0.05, 0, 0.05, 0), col=col, hcol=col)
        cx -= ww + gap


def card(s, x, y, w, h, it, k=0, center=False, style='bar', pt=None):
    """generic card: icon, n(umber label), h, s, x/list, tag, foot"""
    acc = ACC[k % 3]
    s.rect(x, y, w, h, 'FFFFFF', 'roundRect', {'adj': 8000}, line=LINE, lw=0.75, name='Card')
    if style == 'bar':
        s.rect(x + w - 0.07, y + 0.12, 0.07, h - 0.24, acc, name='Card Accent')
    else:
        s.rect(x + 0.12, y, w - 0.24, 0.07, acc, name='Card Accent')
    top = y + 0.14
    pad = 0.2
    ic = it.get('ic')
    al = 'ctr' if center else 'r'
    if ic:
        isz = min(0.5, h * 0.22)
        if center:
            s.rect(x + w / 2 - isz * 0.8, top, isz * 1.6, isz * 1.6, NAVY, 'ellipse', name='Icon Circle')
            s.icon(ic, x + w / 2 - isz * 0.5, top + isz * 0.3, isz, 'w')
            top += isz * 1.6 + 0.08
        else:
            s.icon(ic, x + pad, y + 0.16, isz, 't')
            if w < 3.0:
                top += isz + 0.12
    items = []
    if it.get('n'):
        items.append((it['n'], 'g'))
    if it.get('h'):
        items.append((it['h'], 'h'))
    if it.get('s'):
        items.append((it['s'], 's'))
    for line_ in (it.get('x') or '').split('\n'):
        if line_:
            items.append((line_, 'x'))
    for b in it.get('list', []):
        items.append((b, 'b'))
    foot_h = 0
    if it.get('code'):
        foot_h += 0.75
    if it.get('tag'):
        foot_h += 0.36
    if it.get('foot'):
        foot_h += 0.3
    bh = y + h - top - 0.1 - foot_h
    right_pad = 0.18 if style == 'bar' else 0.14
    left_pad = pad + (0.55 if ic and not center else 0) if False else pad
    tw = w - left_pad - right_pad - 0.05
    s.box('Card Text', x + left_pad, top, tw, bh, items, 22 if center else 18, 8.5, al=al, anchor='ctr' if center else 't',
          ins=(0.02, 0.02, 0.02, 0.02), spacing=0.38, pt=pt)
    s.card_pt = getattr(s, 'last_pt', None)
    fy = y + h - 0.1 - foot_h
    if it.get('code'):
        s.box('Card Code', x + 0.15, fy, w - 0.35, 0.68, [(it['code'], 'x')], 12, 8, al='l', anchor='ctr', fill=SOFT,
              ins=(0.12, 0.03, 0.12, 0.03))
        fy += 0.75
    if it.get('tag'):
        pills(s, [it['tag']], x + 0.15, fy + 0.02, w - 0.3, 0.3, 11, al='ctr' if center else 'r')
        fy += 0.36
    if it.get('foot'):
        s.text(it['foot'], x + 0.15, fy, w - 0.35, 0.28, 10.5, GRAY, False, al)


def grid(n, top, bottom, cols, x0=X0, x1=X1, gap=0.22):
    rows = math.ceil(n / cols)
    cw = (x1 - x0 - gap * (cols - 1)) / cols
    rh = (bottom - top - gap * (rows - 1)) / rows
    out = []
    for i in range(n):
        r, c = divmod(i, cols)
        cnt = min(cols, n - r * cols)
        off = (cols - cnt) * (cw + gap) / 2
        x = x1 - (c + 1) * cw - c * gap - off
        out.append((x, top + r * (rh + gap), cw, rh))
    return out


def ncols(n):
    return {1: 1, 2: 2, 3: 3, 4: 4, 5: 3, 6: 3, 7: 4, 8: 4, 9: 3}.get(n, 4)


# ---------------------------------------------------------------- diagrams (left panel)
def dia(s, d, x, y, w, h):
    kind = d.get('kind')
    if kind == 'chain':
        nodes = d['nodes']
        n = len(nodes)
        bw = min(1.9, (w - 0.5 * (n - 1)) / n)
        gap = (w - bw * n) / max(1, n - 1)
        cy = y + h * 0.42
        for i, nd in enumerate(nodes):
            bx = x + w - (i + 1) * bw - i * gap
            main = i == 1
            s.box('Node', bx, cy - 0.4, bw, 0.8, [(nd[0], 'h')], pt=17, al='ctr', anchor='ctr',
                  fill=TEAL if main else 'FFFFFF', line=TEAL, lw=1.5, hcol='FFFFFF' if main else NAVY)
            if len(nd) > 1:
                s.text(nd[1], bx, cy + 0.45, bw, 0.3, 11.5, GRAY, False, 'ctr')
            if i < n - 1:
                ax = bx - gap
                s.line(bx - 0.06, cy, ax + 0.06, cy, TEAL_D, 1.5, True, head=True)
                if d.get('links'):
                    s.text(d['links'][i], ax, cy - 0.42, gap, 0.28, 10, TEAL_D, False, 'ctr')
        if d.get('cap'):
            s.line(x, cy + 0.9, x + w, cy + 0.9, TEAL, 1, False)
            s.text(d['cap'], x, cy + 0.95, w, 0.3, 11.5, GRAY, False, 'ctr')
    elif kind == 'vflow':
        nodes = d['nodes']
        n = len(nodes)
        bh = min(0.75, (h - 0.5 - 0.35 * (n - 1)) / n)
        gap = (h - 0.4 - bh * n) / max(1, n - 1)
        bw = min(w, 2.6)
        bx = x + (w - bw) / 2
        for i, nd in enumerate(nodes):
            by = y + i * (bh + gap)
            s.box('Flow', bx, by, bw, bh, [(nd, 'h')], pt=13, al='ctr', anchor='ctr', fill=NAVY if i == 1 else 'FFFFFF',
                  line=TEAL, lw=1.25, hcol='FFFFFF' if i == 1 else NAVY)
            if i < n - 1:
                s.line(bx + bw / 2, by + bh + 0.04, bx + bw / 2, by + bh + gap - 0.04, TEAL_D, 2, True)
        if d.get('cap'):
            s.text(d['cap'], x, y + h - 0.32, w, 0.3, 10.5, GRAY, False, 'ctr')
    elif kind == 'hub':
        cx, cy = x + w / 2, y + h / 2 - (0.15 if d.get('cap') else 0)
        r = min(w, h) * 0.34
        nodes = d['nodes']
        sc = max(1.0, min(1.6, min(w / 4.2, h / 3.6)))
        r = min(w / sc, h / sc) * 0.34 * sc
        cr = 0.85 * sc
        s.box('Hub', cx - cr, cy - cr, 2 * cr, 2 * cr, [(p, 'h') for p in d['center'].split(' · ')], pt=13 * min(sc, 1.3), al='ctr', anchor='ctr', fill=TEAL,
              geom='ellipse', hcol='FFFFFF', ins=(0.05, 0.05, 0.05, 0.05))
        for i, nd in enumerate(nodes):
            a = -math.pi / 2 + i * 2 * math.pi / len(nodes) + (math.pi / 4 if len(nodes) == 4 else 0)
            bw, bh = 1.55 * sc, 0.55 * sc
            rx = max(r * 1.35, (cr + bw / 2 + 0.3) / 0.75)
            rx = min(rx, (w / 2 - bw / 2 - 0.05) / 0.71)
            nx, ny = cx + rx * math.cos(a), cy + r * math.sin(a)

            s.box('Spoke', nx - bw / 2, ny - bh / 2, bw, bh, [(p, 'h') for p in nd.split(' · ')], pt=12 * min(sc, 1.3), spacing=0.1, al='ctr', anchor='ctr', fill='FFFFFF',
                  line=TEAL, lw=1.25)
            ex, ey = cx + (cr + 0.05) * math.cos(a), cy + (cr + 0.05) * math.sin(a)
            fx, fy = nx - (bw / 2 + 0.05) * math.cos(a) * 0.9, ny - (bh / 2 + 0.06) * math.sin(a)
            if d.get('inward'):
                s.line(fx, fy, ex, ey, TEAL_D, 1.5, True)
            else:
                s.line(ex, ey, fx, fy, TEAL_D, 1.5, True)
        if d.get('cap'):
            s.text(d['cap'], x, y + h - 0.32, w, 0.3, 11, GRAY, False, 'ctr')
    elif kind == 'nn':
        layers = [4, 6, 6, 3]
        lx = [x + w * (0.12 + 0.25 * i) for i in range(4)]
        pts = []
        for i, n in enumerate(layers):
            ys = [y + 0.3 + (h - 0.9) * (j + 0.5) / n for j in range(n)]
            pts.append([(lx[i], yy) for yy in ys])
        for i in range(3):
            for a in pts[i]:
                for b in pts[i + 1]:
                    s.line(a[0], a[1], b[0], b[1], 'B9C4D6', 0.5, False)
        for i, layer in enumerate(pts):
            for (px, py) in layer:
                s.rect(px - 0.11, py - 0.11, 0.22, 0.22, TEAL if i in (1, 2) else 'FFFFFF', 'ellipse', line=TEAL_D, lw=1)
        labs = d.get('labels', [])
        if labs:
            s.text(labs[0], lx[0] - 0.6, y + h - 0.4, 1.2, 0.3, 10.5, GRAY, False, 'ctr')
            s.text(labs[1], (lx[1] + lx[2]) / 2 - 0.8, y + h - 0.4, 1.6, 0.3, 10.5, TEAL_D, True, 'ctr')
            s.text(labs[2], lx[3] - 0.6, y + h - 0.4, 1.2, 0.3, 10.5, GRAY, False, 'ctr')
    elif kind == 'merge':
        ins_ = d['ins']
        bw = w * 0.4
        for i, (a, b) in enumerate(ins_):
            by = y + 0.2 + i * (h * 0.48)
            s.box('In', x + w - bw, by, bw, h * 0.36, [(a, 'h'), (b, 'g')], 13, 8, al='ctr', anchor='ctr', fill='FFFFFF',
                  line=TEAL, lw=1.25)
            s.line(x + w - bw - 0.05, by + h * 0.18, x + w * 0.5, y + h * 0.45, TEAL_D, 1.5, True)
        mw = w * 0.36
        s.box('Mid', x + w * 0.12, y + h * 0.33, mw, h * 0.26, [(d['mid'][0], 'h'), (d['mid'][1], 'g')], 13, 8, al='ctr',
              anchor='ctr', fill=TEAL, hcol='FFFFFF', col='FFFFFF')
        s.line(x + w * 0.3, y + h * 0.6, x + w * 0.3, y + h * 0.78, TEAL_D, 1.5, True)
        s.box('Out', x + w * 0.08, y + h * 0.8, w * 0.44, h * 0.16, [(d['out'], 'h')], 13, 8, al='ctr', anchor='ctr',
              fill=TINT, line=TEAL)
    elif kind == 'window':
        s.rect(x, y + 0.1, w - 0.45, h * 0.55, TINT, 'roundRect', {'adj': 6000}, line=TEAL, lw=1.5)
        s.box('Lab', x + (w - 0.45) / 2 - 0.9, y - 0.05, 1.8, 0.32, [(d['lab'], 'h')], pt=12, al='ctr', anchor='ctr',
              fill=TEAL, hcol='FFFFFF', adj={'adj': 50000}, ins=(0.02, 0, 0.02, 0))
        docs = d['docs']
        dw = (w - 0.45 - 0.4 - 0.15 * (len(docs) - 1)) / len(docs)
        for i, dd in enumerate(docs):
            s.box('Doc', x + 0.2 + i * (dw + 0.15), y + 0.42, dw, h * 0.55 - 0.5, [(dd, 'h')], 11, 8, al='ctr',
                  anchor='ctr', fill='FFFFFF', line=LINE)
        s.rect(x + w - 0.3, y + 0.1, 0.16, h * 0.55, SOFT, 'roundRect', line=LINE)
        s.rect(x + w - 0.3, y + 0.1 + h * 0.15, 0.16, h * 0.4, TEAL, 'roundRect')
        s.add(sp_xml(s.ids, 'Side', x + w - 0.22 - h * 0.25, y + 0.1 + h * 0.275 - 0.15, h * 0.5, 0.3, 'rect', rot=-90,
                     body=P(d['side'], 9, GRAY, False, 'ctr'), anchor='ctr', ins=(0, 0, 0, 0), txbox=True))
        s.line(x + (w - 0.45) / 2, y + h * 0.67, x + (w - 0.45) / 2, y + h * 0.8, NAVY, 2.5, True)
        s.box('Out', x + (w - 0.45) / 2 - 1.1, y + h * 0.82, 2.2, 0.4, [(d['out'], 'h')], pt=12, al='ctr', anchor='ctr',
              fill=TEAL, hcol='FFFFFF')
    elif kind == 'tip':
        s.rect(x, y + h * 0.3, w, h * 0.45, ORANGE, 'roundRect', {'adj': 12000})
        s.box('Tip', x + 0.25, y + h * 0.3, w - 0.5, h * 0.45, [(d['lab'], 'h'), (d['x'], 't')], 22, 11, al='r', anchor='ctr',
              hcol='FFFFFF', ins=(0.02, 0, 0.02, 0))
    elif kind == 'pyramid':
        lv = d['levels']
        n = len(lv)
        lh = (h - 0.3) / n
        cx = x + w / 2 - (0.4 if d.get('mark') else 0)
        for k, (a, b, c) in enumerate(lv):
            yy = y + 0.15 + k * lh
            tw_ = w * 0.3 + (w * 0.7 - 0.9) * (k + 1) / n
            if k == 0:
                s.box('Lvl', cx - tw_ / 2, yy, tw_, lh - 0.04, [(a, 'h'), (b, 'g')], 13, 8, al='ctr', anchor='b',
                      fill=c, geom='triangle', hcol='FFFFFF', col='FFFFFF', ins=(0.02, 0, 0.02, 0.04))
            else:
                s.box('Lvl', cx - tw_ / 2, yy, tw_, lh - 0.04, [(a, 'h'), (b, 'g')], 14, 8, al='ctr', anchor='ctr',
                      fill=c, geom='trapezoid', adj={'adj': int(25000 * (n - 1) / n * 2)}, hcol='FFFFFF', col='FFFFFF',
                      ins=(0.02, 0, 0.02, 0))
        if d.get('mark'):
            s.box('Mark', x + w - 1.0, y + 0.15, 1.0, 2 * lh, [(d['mark'], 'g')], 11, 8, al='ctr', anchor='ctr',
                  line=TEAL_D, ins=(0.04, 0, 0.04, 0))
    elif kind == 'semantic':
        g1, g2 = d['groups']
        # cluster 1 (left-mid), cluster 2 (right-top), far point
        def cluster(cx, cy, rw, rh, words, lab, main):
            s.rect(cx - rw, cy - rh, 2 * rw, 2 * rh, TINT if main else 'FFF6EA', 'ellipse', line=TEAL if main else ORANGE, lw=1.25)
            for j, wd in enumerate(words):
                s.text(wd, cx - rw, cy - rh + 0.2 + j * (2 * rh - 0.4) / len(words), 2 * rw, (2 * rh - 0.4) / len(words),
                       15, TEAL_D if main else OR_D, True, 'ctr')
            s.text(lab, cx - rw - 0.2, cy + rh + 0.02, 2 * rw + 0.4, 0.3, 10.5, GRAY, False, 'ctr')
        cluster(x + w * 0.3, y + h * 0.45, 1.25, 0.95, g1['words'], g1['lab'], True)
        cluster(x + w * 0.72, y + h * 0.3, 1.25, 0.8, g2['words'], g2['lab'], False)
        s.line(x + w * 0.3 + 1.25, y + h * 0.42, x + w * 0.72 - 1.25, y + h * 0.32, GRAY, 1, False, dash='dash')
        fx, fy = x + w * 0.85, y + h * 0.85
        s.box('Far', fx - 0.8, fy - 0.25, 1.6, 0.5, [(d['far'], 'h')], pt=13, al='ctr', anchor='ctr', fill=SOFT,
              line=LINE, geom='ellipse', hcol=GRAY)
        s.line(x + w * 0.3 + 1.0, y + h * 0.62, fx - 0.8, fy, GRAY, 1, False, dash='dash')
        s.text(d['farlab'], x + w * 0.42, y + h * 0.8, 2.8, 0.3, 10, GRAY, False, 'ctr')


# ---------------------------------------------------------------- layouts
def L_cover(s, sp):
    s.layout = 1
    s.dark = True
    s.text(sp.get('tag', ''), 5.6, 1.25, 7.2, 0.4, 14, TEAL, True, 'r', name='Tag')
    s.add(sp_xml(s.ids, 'Title', 5.6, 1.7, 7.2, 1.9, anchor='b', ins=(0.02, 0, 0.02, 0), ph='ctrTitle',
                 body=P(sp['t'], 38, 'FFFFFF', True, 'r', line=0.95)))
    s.rect(11.6, 3.75, 1.2, 0.07, TEAL)
    s.rect(11.3, 3.75, 0.22, 0.07, ORANGE)
    items = [(sp.get('en', ''), 's')]
    if sp.get('sec'):
        items.append((sp['sec'], 'g'))
    s.box('Subtitle', 5.6, 3.95, 7.2, 1.0, items, 20, 11, al='r', ins=(0.02, 0, 0.02, 0), col='C9CBF0')
    if sp.get('x'):
        s.box('Desc', 5.6, 5.0, 7.2, 0.9, [(sp['x'], 'x')], 14, 10, al='r', ins=(0.02, 0, 0.02, 0), col='C9CBF0')
    if sp.get('obj'):
        s.box('Objectives', 5.6, 4.95, 7.2, 1.85, [('מטרות למידה', 's')] + [(o, 'b') for o in sp['obj']], 13, 8, al='r',
              ins=(0.02, 0, 0.02, 0), col='E6E8F5', hcol='FFFFFF')
    meta = ' | '.join(v for v in (sp.get('cert'), sp.get('date')) if v)
    if meta:
        s.text(meta, 5.6, 6.0, 7.2, 0.3, 11, 'A9B1C2', False, 'r')


def L_section(s, sp):
    pw = 4.4
    s.rect(X0, 0.95, pw, 5.8, NAVY, 'roundRect', {'adj': 6000}, name='Section Panel')
    s.rect(X0 + pw / 2 - 0.75, 1.45, 1.5, 1.5, 'FFFFFF', 'ellipse')
    s.icon(sp.get('ic', 'layers'), X0 + pw / 2 - 0.42, 1.78, 0.84, 't')
    s.text('הנושא הבא', X0 + 0.3, 3.35, pw - 0.6, 0.35, 13, TEAL, True, 'ctr')
    s.text(sp.get('k', ''), X0 + 0.3, 3.7, pw - 0.6, 0.9, 44, TEAL, True, 'ctr')
    if sp.get('ex'):
        s.text('תרגיל מעשי', X0 + 0.3, 4.65, pw - 0.6, 0.5, 20, 'FFFFFF', True, 'ctr')
    x0 = X0 + pw + 0.5
    s.add(sp_xml(s.ids, 'Title', x0, 1.0, X1 - x0, 0.9, anchor='ctr', ins=(0.02, 0, 0.02, 0), ph='title',
                 body=P(sp['t'], 34, NAVY, True, 'r')))
    s.rect(X1 - 1.15, 1.95, 1.15, 0.06, TEAL)
    s.rect(X1 - 1.42, 1.95, 0.2, 0.06, ORANGE)
    s.box('Sub', x0, 2.15, X1 - x0, 1.0, [(sp.get('en', ''), 's'), (sp.get('x', ''), 'x')], 18, 11, al='r',
          ins=(0.02, 0, 0.02, 0))
    if sp.get('pills'):
        pills(s, sp['pills'], x0, 3.6, X1 - x0, 0.45, 15)
    if sp.get('ex'):
        exbtn(s, sp, 4.5)
    vs = sp.get('vs') or []
    if vs:
        gap = 1.2
        bw = (X1 - x0 - gap) / 2
        for k, v in enumerate(vs[:2]):
            bx = X1 - (k + 1) * bw - k * gap
            s.box('VS', bx, 3.6, bw, 2.2, [(v['h'], 't'), (v.get('s', ''), 'g'), (v.get('x', ''), 's')], 30, 11,
                  al='ctr', anchor='ctr', fill='FFFFFF' if k else TINT, line=TEAL, lw=1.5)
        s.box('VSL', X1 - bw - gap + 0.2, 4.35, gap - 0.4, gap - 0.4, [(sp.get('vslab', 'VS'), 'h')], pt=12, al='ctr',
              anchor='ctr', fill=ORANGE, geom='ellipse', hcol='FFFFFF', ins=(0, 0, 0, 0))


def L_cards(s, sp, top):
    bottom = note(s, sp.get('note'))
    items = sp['items']
    if sp.get('top_note'):
        tn = sp['top_note']
        note(s, tn, top, 0.62)
        top += 0.8
    if sp.get('lead'):
        ld = sp['lead']
        lit = [(ld['h'], 'h')] + ([(ld['x'], 'x')] if ld.get('x') else [])
        lh = 0.85 if ld.get('x') else 0.45
        s.box('Lead', X0 + 1.2, top, X1 - X0 - 2.4, lh, lit, 18, 10, al='ctr',
              anchor='ctr', fill=TINT if ld.get('x') else None, line=TEAL if ld.get('x') else None)
        top += lh + 0.2
    if sp.get('example'):
        ex = sp['example']
        nl = ex['code'].count('\n') + 1 + (1 if ex.get('lab') else 0)
        eh = 0.3 + 0.36 * nl
        bottom -= eh + 0.15
        s.box('Example', X0 + 1.5, bottom + 0.12, X1 - X0 - 3.0, eh, ([(ex['lab'], 's')] if ex.get('lab') else []) + [(l, 'x' if re.search('[א-ת]', l) else 'c') for l in ex['code'].split('\n')], 16, 11,
              al='r', anchor='ctr', fill=SOFT, line=LINE)
    if sp.get('uses'):
        bottom -= 0.95
        u = sp['uses']
        s.text(u['h'], X0, bottom + 0.12, X1 - X0, 0.3, 13, TEAL_D, True, 'r')
        pills(s, u['pills'], X0, bottom + 0.48, X1 - X0, 0.4, 13)
    if sp.get('flow'):
        # flow column on the left
        fw = 3.0
        dia(s, {'kind': 'vflow', 'nodes': sp['flow']}, X0, top, fw, bottom - top)
        x1 = X1
        x0 = X0 + fw + 0.35
    else:
        x0, x1 = X0, X1
    if sp.get('cap'):
        bottom -= 0.42
        cap(s, sp['cap'], bottom + 0.05)
    if sp.get('lead2'):
        bottom -= 1.0
        l2 = sp['lead2']
        s.box('Result', X0 + 2.5, bottom + 0.15, X1 - X0 - 5.0, 0.8, [(l2['h'], 't'), (l2['x'], 's')], 22, 10, al='ctr',
              anchor='ctr', fill=TINT, line=TEAL, lw=1.5)
        s.line(W / 2, bottom - 0.05, W / 2, bottom + 0.13, TEAL_D, 2.5, True)
    if sp.get('arrow'):
        bottom -= 0.3
    n = len(items)
    cols = sp.get('cols') or (ncols(n) if not sp.get('flow') else (2 if n > 3 else 1))
    rows = math.ceil(n / cols)
    def nat(i):
        return (0.9 + (0.55 if i.get('ic') else 0) + 0.32 * len(i.get('list', [])) + len(i.get('x', '')) / (55 if cols <= 2 else 30) * 0.3
                + (0.4 if i.get('tag') else 0) + (0.3 if i.get('foot') else 0) + (0.8 if i.get('code') else 0) + (0.3 if i.get('s') else 0))
    maxh = max(nat(i) for i in items) * 1.25 * rows + 0.22 * (rows - 1)
    if bottom - top > maxh:
        pad_ = (bottom - top - maxh) / 2
        top, bottom = top + pad_, bottom - pad_
    cells = grid(n, top, bottom, cols, x0, x1, 1.1 if sp.get('mid') and n == 2 else 0.22)
    center = cols >= 3 and all(len(i.get('x', '')) < 70 and not i.get('list') for i in items)
    import copy
    pts = []
    for k, (it, c) in enumerate(zip(items, cells)):
        tmp = copy.deepcopy(s)
        card(tmp, *c, it, k, center=center, style='top' if center else 'bar')
        pts.append(tmp.card_pt)
    upt = min(p for p in pts if p) if any(pts) else None
    for k, (it, c) in enumerate(zip(items, cells)):
        card(s, *c, it, k, center=center, style='top' if center else 'bar', pt=upt)
    if sp.get('mid') and n == 2:
        x, y, w, h = cells[1]
        gx = x + w + 0.55
        s.box('Mid', gx - 0.42, y + h / 2 - 0.42, 0.84, 0.84, [(sp['mid'], 'h')], pt=15, al='ctr', anchor='ctr', fill=ORANGE,
              geom='ellipse', hcol='FFFFFF', ins=(0, 0, 0, 0))
    if sp.get('arrow'):
        s.line(X1 - 0.2, bottom + 0.18, X0 + 0.2, bottom + 0.18, TEAL_D, 2, True)


def L_blocks(s, sp, top):
    bottom = note(s, sp.get('note'))
    has_dia = sp.get('dia')
    x0 = X0 + 5.0 if has_dia else X0 + 1.0
    if has_dia:
        dia(s, sp['dia'], X0, top + 0.2, 4.6, bottom - top - 0.2)
    blocks = sp['blocks']
    # weights
    wts = []
    for b in blocks:
        if b.get('code'):
            wts.append(1.5 + 0.3 * b['code'].count('\n'))
        elif b.get('pills'):
            wts.append(0.8 + 0.35 * (len(b['pills']) > 4))
        elif b.get('logos'):
            wts.append(1.0)
        else:
            wts.append(1.0 + len(b.get('x', '') + b.get('t', '')) / 160)
    tot = sum(wts)
    avail = bottom - top - 0.18 * (len(blocks) - 1)
    y = top
    for k, (b, wt) in enumerate(zip(blocks, wts)):
        bh = avail * wt / tot
        s.rect(x0, y, X1 - x0, bh, 'FFFFFF', 'roundRect', {'adj': 9000}, line=LINE, lw=0.75)
        s.rect(X1 - 0.07, y + 0.1, 0.07, bh - 0.2, ACC[k % 3])
        s.text(b['h'], x0 + 0.2, y + 0.06, X1 - x0 - 0.45, 0.32, 13, TEAL_D, True, 'r')
        iy = y + 0.4
        ih = bh - 0.48
        if b.get('code'):
            gh = 0.32 if b.get('g') else 0
            code_panel(s, x0 + 0.2, iy, X1 - x0 - 0.45, ih - gh, b['code'], '', 15)
            if b.get('g'):
                s.text(b['g'], x0 + 0.2, iy + ih - 0.3, X1 - x0 - 0.45, 0.3, 11, GRAY, False, 'r')
        elif b.get('pills'):
            pills(s, b['pills'], x0 + 0.2, iy + max(0, ih - 0.42) / 2 - 0.05, X1 - x0 - 0.5, 0.42, 14)
        elif b.get('logos'):
            lg = b['logos']
            lw_ = (X1 - x0 - 0.5) / len(lg)
            for j, (a, c) in enumerate(lg):
                s.box('Logo', X1 - 0.3 - (j + 1) * lw_, iy, lw_ - 0.1, ih, [(a, 'h'), (c, 'g')], 18, 9, al='ctr',
                      anchor='ctr', hcol=TEAL_D)
        else:
            items = []
            if b.get('t'):
                items.append((b['t'], 'h'))
            if b.get('x'):
                items.append((b['x'], 'x'))
            if b.get('x2'):
                items.append((b['x2'], 'g'))
            cw = X1 - x0 - 0.45
            if b.get('chain'):
                cw -= 3.2
                ch = b['chain']
                bx = x0 + 0.2
                for j, c in enumerate(reversed(ch)):
                    s.box('Chip', bx + j * 1.6, iy + ih / 2 - 0.18, 1.35, 0.36, [(c, 'k')], pt=11, al='ctr',
                          anchor='ctr', fill=TINT, col=TEAL_D, hcol=TEAL_D, adj={'adj': 50000}, ins=(0.02, 0, 0.02, 0))
                s.line(bx + 1.38, iy + ih / 2, bx + 1.57, iy + ih / 2, TEAL_D, 1.25, True)
            s.box('Block Text', X1 - 0.25 - cw, iy - 0.02, cw, ih, items, 17, 9, al='r', anchor='ctr',
                  ins=(0.02, 0, 0.02, 0))
        y += bh + 0.18


def L_steps(s, sp, top):
    bottom = note(s, sp.get('note'))
    if sp.get('cap'):
        bottom -= 0.45
        cap(s, sp['cap'], bottom + 0.08)
    if sp.get('lead'):
        ld = sp['lead']
        its = [(ld['x'], 'x')] + ([(ld['g'], 's')] if ld.get('g') else [])
        s.box('Lead', X0 + 3.0, top, X1 - X0 - 3.0, 0.95, its, 17, 10, al='r', anchor='ctr', fill=TINT,
              ins=(0.25, 0.04, 0.25, 0.04))
        top += 1.15
    if sp.get('lead_after'):
        la = sp['lead_after']
        bottom -= 1.15
        s.box('After', X0 + 1.5, bottom + 0.15, X1 - X0 - 3.0, 1.0, [(la['h'], 'h')] + [(t, 'b') for t in la['items']], 16, 9,
              al='r', anchor='ctr', fill=TINT, ins=(0.25, 0.04, 0.25, 0.04))
    if sp.get('groups'):
        bottom -= 0.6
    steps = sp['steps']
    n = len(steps)
    gap = 0.42 if not sp.get('arrow_lab') else 0.75
    if n >= 7:
        gap = 0.22
    bw = (X1 - X0 - gap * (n - 1)) / n
    longest = max(len(' '.join(st[:3])) for st in steps)
    bh = min(bottom - top, (1.9 if longest < 40 else 2.8 if longest < 90 else 3.6) + (0.95 if sp.get('ics') else 0))
    y = top + (bottom - top - bh) / 2
    ics = sp.get('ics') or []
    for i, st in enumerate(steps):
        x = X1 - (i + 1) * bw - i * gap
        s.rect(x, y, bw, bh, 'FFFFFF', 'roundRect', {'adj': 7000}, line=LINE, lw=0.75)
        s.rect(x, y, bw, 0.5, NAVY, 'round2SameRect', {'adj1': 30000, 'adj2': 0})
        lab = st[3] if len(st) > 3 else f'{i + 1:02d}'
        s.text(lab, x, y + 0.05, bw, 0.4, 14, TEAL, True, 'ctr')
        ty = y + 0.62
        if i < len(ics) and ics[i]:
            s.rect(x + bw / 2 - 0.42, ty, 0.84, 0.84, TINT, 'ellipse')
            s.icon(ics[i], x + bw / 2 - 0.25, ty + 0.17, 0.5, 't')
            ty += 0.95
        items = [(st[0], 'h')]
        if len(st) > 1 and st[1]:
            items.append((st[1], 's'))
        if len(st) > 2 and st[2]:
            items.append((st[2], 'x'))
        foot = 0
        if len(st) > 3 and len(st) > 2:
            pass
        s.box('Step Text', x + 0.12, ty, bw - 0.24, y + bh - ty - 0.12, items, 17, 9, al='ctr', anchor='t',
              ins=(0.02, 0.02, 0.02, 0.02))
        if i < n - 1:
            s.line(x - 0.06, y + bh / 2, x - gap + 0.06, y + bh / 2, ORANGE, 2.25, True)
            if sp.get('arrow_lab'):
                s.text(sp['arrow_lab'], x - gap, y + bh / 2 - 0.36, gap, 0.28, 9, OR_D, False, 'ctr')
    for gi, (lab, a, b) in enumerate(sp.get('groups', [])):
        xr = X1 - a * (bw + gap)
        xl = X1 - (b + 1) * bw - b * gap
        gy = y + bh + 0.15
        s.line(xl + 0.05, gy, xr - 0.05, gy, ACC[gi % 3], 2.5, False)
        s.text(lab, xl, gy + 0.08, xr - xl, 0.34, 13, ACC[gi % 3] if gi != 2 else NAVY, True, 'ctr')


def L_table(s, sp, top, head=None, rows=None, qs=None):
    bottom = note(s, sp.get('note'))
    if sp.get('cap'):
        bottom -= 0.45
        cap(s, sp['cap'], bottom + 0.08)
    if qs:
        bottom -= 1.15
        qw = (X1 - X0 - 0.3 * (len(qs) - 1)) / len(qs)
        for k, q in enumerate(qs):
            x = X1 - (k + 1) * qw - k * 0.3
            s.box('Question', x, bottom + 0.2, qw, 0.9, [(q, 'x')], 15, 9, al='r', anchor='ctr', fill='FFFFFF', line=LINE,
                  shadow=True)
            s.rect(x + qw - 0.07, bottom + 0.3, 0.07, 0.7, ORANGE)
    head = head or sp['head']
    rows = rows or sp['rows']
    nc = len(head)
    nr = len(rows) + 1
    tw = X1 - X0 - (0.6 if nc <= 3 else 0.2)
    # first column wider
    cw = [tw * (1.4 if j == 0 else 1.0) for j in range(nc)]
    sc = tw / sum(cw)
    cw = [c * sc for c in cw]
    rh = min(0.72, (bottom - top) / nr)
    x0 = X0 + (X1 - X0 - tw) / 2
    y = top + max(0, (bottom - top - rh * nr) / 2) * 0.3
    for r in range(nr):
        x = x0 + tw
        for j in range(nc):
            x -= cw[j]
            t = head[j] if r == 0 else rows[r - 1][j]
            star = t.startswith('★')
            t = t.replace('★', '').strip()
            if r == 0:
                fill, col, b = NAVY, 'FFFFFF', True
            elif j == 0:
                fill, col, b = SOFT, NAVY, True
            else:
                fill, col, b = ('FFFFFF' if r % 2 else 'FAFBFD'), BODY, False
            if star:
                fill, col, b = TINT, TEAL_D, True
            if t in ('✓', '✗'):
                col = GOOD if t == '✓' else BAD
                b = True
            pt = 15 if nr <= 5 else 13
            while pt > 9 and wlen(t, pt, b) > cw[j] - 0.2:
                pt -= 0.5
            if not t and r > 0:
                s.box('Cell', x, y + r * rh, cw[j], rh, None, fill=fill, line=LINE, geom='rect')
                s.rect(x + 0.2, y + r * rh + 0.14, cw[j] - 0.4, rh - 0.28, None, 'roundRect', line='B9C4D6', dash='dash')
                continue
            s.box('Cell', x, y + r * rh, cw[j], rh, [(t, 'k' if False else 'x')], pt=pt, al='ctr', anchor='ctr',
                  fill=fill, line=LINE, geom='rect', col=col, ins=(0.06, 0.02, 0.06, 0.02))
            if b and t:
                pass


def L_vs(s, sp, top):
    bottom = note(s, sp.get('note'))
    cols = sp['cols']
    gap = 1.0
    cw = (X1 - X0 - gap) / 2
    for k, c in enumerate(cols):
        x = X1 - (k + 1) * cw - k * gap
        main = c.get('main') or k == 0
        s.rect(x, top, cw, bottom - top, 'FFFFFF', 'roundRect', {'adj': 6000}, line=TEAL if main else LINE, lw=1.5 if main else 0.75)
        s.rect(x, top, cw, 0.85 if c.get('s') else 0.62, NAVY if main else 'E9ECF3', 'round2SameRect', {'adj1': 20000, 'adj2': 0})
        hi = [(c['h'], 't')] + ([(c['s'], 's')] if c.get('s') else [])
        s.box('Head', x + 0.2, top + 0.02, cw - 0.4, 0.8 if c.get('s') else 0.58, hi, 22, 11, al='ctr', anchor='ctr',
              hcol='FFFFFF' if main else NAVY, ins=(0.02, 0, 0.02, 0))
        ry = top + (1.0 if c.get('s') else 0.75)
        rows = c['rows']
        capy = 0.45 if c.get('cap') else 0
        rh = (bottom - ry - 0.15 - capy) / len(rows)
        for j, (a, b) in enumerate(rows):
            yy = ry + j * rh
            s.text(a, x + cw / 2, yy, cw / 2 - 0.3, rh, 15, GRAY, False, 'r')
            s.text(b, x + 0.3, yy, cw / 2 - 0.3, rh, 16, NAVY, True, 'r')
            if j < len(rows) - 1:
                s.line(x + 0.25, yy + rh, x + cw - 0.25, yy + rh, LINE, 0.75, False)
        if c.get('cap'):
            s.text(c['cap'], x + 0.2, bottom - 0.5, cw - 0.4, 0.4, 12, GRAY, False, 'ctr')
    cy = (top + bottom) / 2
    s.box('VS', W / 2 - 0.42 + (X0 + X1 - W) / 2, cy - 0.42, 0.84, 0.84, [('VS', 'h')], pt=18, al='ctr', anchor='ctr',
          fill=ORANGE, geom='ellipse', hcol='FFFFFF', ins=(0, 0, 0, 0))


def L_proscons(s, sp, top):
    bottom = note(s, sp.get('note'))
    gap = 0.5
    cw = (X1 - X0 - gap) / 2
    nmax = max(len(sp['pros']['items']), len(sp['cons']['items']))
    full = 0.95 + nmax * 1.15 + 0.2
    if full < bottom - top:
        top += (bottom - top - full) / 2
        bottom = top + full
    for k, key in enumerate(('pros', 'cons')):
        c = sp[key]
        x = X1 - (k + 1) * cw - k * gap
        good = key == 'pros'
        col = GOOD if good else BAD
        s.rect(x, top, cw, bottom - top, 'FFFFFF', 'roundRect', {'adj': 5000}, line=col, lw=1.5)
        s.box('Head', x + 0.2, top + 0.08, cw - 0.4, 0.75, [(c['h'], 't'), (c.get('s', ''), 'g')], 22, 10, al='ctr',
              anchor='ctr', hcol=col, ins=(0.02, 0, 0.02, 0))
        s.icon('check' if good else 'warn', x + cw - 0.75, top + 0.2, 0.45, 't' if good else 'o')
        its = c['items']
        ry = top + 0.95
        rh = min(1.15, (bottom - ry - 0.15) / len(its))
        for j, (a, b) in enumerate(its):
            s.box('Item', x + 0.2, ry + j * rh + 0.05, cw - 0.4, rh - 0.1, [(a, 'h'), (b, 'x')], 16, 9, al='r', anchor='ctr',
                  fill=SOFT, ins=(0.18, 0.04, 0.18, 0.04))


def L_timeline(s, sp, top):
    bottom = note(s, sp.get('note'))
    items = sp['items']
    n = len(items)
    gap = 0.28
    cw = (X1 - X0 - gap * (n - 1)) / n
    ly = top + 0.55
    s.line(X0 + cw / 2, ly, X1 - cw / 2, ly, TEAL, 3, False)
    # chronological: oldest on the right (RTL reading)
    for i, it in enumerate(items):
        x = X1 - (i + 1) * cw - i * gap
        cur = it.get('cur')
        s.rect(x + cw / 2 - 0.17, ly - 0.17, 0.34, 0.34, ORANGE if cur else NAVY, 'ellipse', line='FFFFFF', lw=2)
        if cur and sp.get('here'):
            s.text('★ ' + sp['here'], x, ly - 0.55, cw, 0.3, 12, OR_D, True, 'ctr')
        y = ly + 0.45
        s.rect(x, y, cw, bottom - y, TINT if cur else 'FFFFFF', 'roundRect', {'adj': 7000}, line=TEAL if cur else LINE,
               lw=1.75 if cur else 0.75)
        s.box('Era', x + 0.12, y + 0.12, cw - 0.24, bottom - y - 0.24,
              [(it['d'], 'g'), (it['h'], 't'), (it['s'], 's')] + [(p, 'x') for p in it.get('x', '').split(' · ')], 18, 9,
              al='ctr', anchor='ctr', spacing=0.3)


def code_panel(s, x, y, w, h, code, label='', maxpt=16, shrink=True):
    lines0 = code.split('\n')
    need = sum(max(1, math.ceil(wlen(l, maxpt, 0) * 1.12 / (w - 0.5))) for l in lines0) * maxpt * 1.3 / 72 + (0.75 if label or h > 1.6 else 0.3)
    if shrink and need < h:
        y += (h - need) / 2
        h = need
    s.rect(x, y, w, h, NAVY, 'roundRect', {'adj': 4000})
    small = h < 1.25 and not label
    if not small:
        for k, c in enumerate(('E0475B', 'F3B811', '12A37A')):
            s.rect(x + 0.2 + k * 0.22, y + 0.16, 0.14, 0.14, c, 'ellipse')
    if label:
        s.text(label, x + 0.95, y + 0.06, w - 1.1, 0.34, 11, 'A9B1C2', False, 'l')
    lines = code.split('\n')
    iw = w - 0.5
    pt = maxpt
    def nlines(p):
        return sum(max(1, math.ceil(wlen(l, p, 0) * 1.12 / iw)) for l in lines)
    hd = 0.2 if small else 0.6
    while pt > 8.5 and nlines(pt) * pt * 1.3 / 72 > h - hd:
        pt -= 0.5
    body = ''
    for ln in lines:
        rtl = heb(ln)
        m = re.match(r'^(IF|THEN|ELSE|AND|OR|Given|When|Then|And)(\s+)(.*)$', ln)
        kv = re.match(r'^([A-Za-z][A-Za-z ]{1,20}):(\s*)(.*)$', ln)
        if m:
            body += (f'<a:p><a:pPr algn="l" rtl="0"/>' + run(m.group(1) + ' ', pt, '14DACD', True, MONO) +
                     run(m.group(3), pt, 'F7B267' if m.group(1) == 'IF' else 'FFFFFF', False, MONO) +
                     f'<a:endParaRPr lang="en-US" sz="{int(pt * 100)}"/></a:p>')
        elif kv and not rtl:
            body += (f'<a:p><a:pPr algn="l" rtl="0"/>' + run(kv.group(1) + ': ', pt, '14DACD', True, MONO) +
                     (run(kv.group(3), pt, 'FFFFFF', False, MONO) if kv.group(3) else '') +
                     f'<a:endParaRPr lang="en-US" sz="{int(pt * 100)}"/></a:p>')
        else:
            body += (f'<a:p><a:pPr algn="{"r" if rtl else "l"}" rtl="{1 if rtl else 0}"/>' +
                     (run(ln, pt, 'FFFFFF', False, 'Arial' if rtl else MONO) if ln else '') +
                     f'<a:endParaRPr lang="en-US" sz="{int(pt * 100)}"/></a:p>')
    s.add(sp_xml(s.ids, 'Code', x + 0.25, y + (0.08 if small else 0.45), w - 0.4, h - (0.16 if small else 0.55), 'rect', body=body, anchor='ctr',
                 ins=(0.02, 0.02, 0.02, 0.02), txbox=True))


def L_code_side(s, sp, top):
    bottom = note(s, sp.get('note'))
    cw = 6.0
    x = X0
    ch = bottom - top
    if sp.get('code_pills'):
        ch -= 0.6
        pills(s, sp['code_pills'], x, top + ch + 0.15, cw, 0.4, 12, al='ctr')
    code_panel(s, x, top, cw, ch, sp['code'], sp.get('code_t', ''), 18)
    blocks = sp['blocks']
    x0 = X0 + cw + 0.4
    wts = [1.0 + 0.35 * len(b.get('list', [])) + len(b.get('x', '')) / 120 for b in blocks]
    avail = bottom - top - 0.2 * (len(blocks) - 1)
    y = top
    natural = sum(0.75 + 0.33 * len(b.get('list', [])) + len(b.get('x', '')) / 60 * 0.3 for b in blocks) * 1.3
    if natural < avail:
        y += (avail - natural) / 2
        avail = natural
    for k, (b, wt) in enumerate(zip(blocks, wts)):
        bh = avail * wt / sum(wts)
        tone = b.get('tone')
        col = {'good': GOOD, 'bad': BAD, 'warn': ORANGE}.get(tone, TEAL_D)
        s.rect(x0, y, X1 - x0, bh, 'FFF6EA' if tone == 'warn' else 'FFFFFF', 'roundRect', {'adj': 8000}, line=LINE)
        s.rect(X1 - 0.07, y + 0.1, 0.07, bh - 0.2, col)
        items = [(b['tag'], 'o' if tone in ('bad', 'warn') else 's')]
        for ln in b.get('x', '').split('\n'):
            if ln:
                items.append((ln, 'x'))
        items += [(t, 'b') for t in b.get('list', [])]
        s.box('Block', x0 + 0.2, y + 0.05, X1 - x0 - 0.45, bh - 0.1, items, 18, 9, al='r', anchor='ctr',
              ins=(0.02, 0, 0.02, 0))
        y += bh + 0.2


def L_def_x(s, sp, top):
    """definition box + something under it"""
    bottom = note(s, sp.get('note'))
    d = sp['def']
    items = [(d['h'], 's')]
    if d.get('t'):
        items.append((d['t'], 'h'))
    items.append((d['x'], 'x'))
    if d.get('x2'):
        items.append((d['x2'], 'g'))
    dh = 0.5 + 0.38 * len(items)
    dx0 = X0 + (4.6 if sp['L'] in ('def_list',) else 0.8)
    s.rect(dx0, top, X1 - dx0, dh, TINT, 'roundRect', {'adj': 9000})
    s.rect(X1 - 0.08, top + 0.1, 0.08, dh - 0.2, TEAL)
    s.box('Definition', dx0 + 0.25, top + 0.05, X1 - dx0 - 0.5, dh - 0.1, items, 18, 10, al='r', anchor='ctr',
          ins=(0.02, 0, 0.02, 0))
    y = top + dh + 0.25
    L = sp['L']
    if L == 'def_tiles':
        tiles = sp['tiles']
        n = len(tiles)
        gap = 0.2
        tw = (X1 - X0 - 0.8 - gap * (n - 1)) / n
        th = min(2.1, bottom - y - 0.1)
        y += (bottom - y - th) / 2
        ic = {'טקסט': 'text', 'קוד': 'code', 'תמונות': 'image', 'קול': 'audio', 'וידאו': 'video', 'מסמכים': 'docs'}
        for i, t in enumerate(tiles):
            x = X1 - (i + 1) * tw - i * gap
            s.rect(x, y, tw, th, 'FFFFFF', 'roundRect', {'adj': 10000}, line=LINE)
            s.rect(x + 0.15, y, tw - 0.3, 0.06, ACC[i % 3])
            s.icon(ic.get(t, 'file'), x + tw / 2 - 0.3, y + 0.25, 0.6, 't')
            s.text(t, x, y + th - 0.6, tw, 0.45, 18, NAVY, True, 'ctr')
    elif L == 'tokens':
        s.text(sp['ex_lab'], X0, y, X1 - X0, 0.3, 12, GRAY, False, 'ctr')
        s.text(sp['ex_t'], X0, y + 0.3, X1 - X0, 0.45, 20, NAVY, True, 'ctr')
        toks = sp['tokens']
        tw = 1.45
        gap = 0.18
        tot = len(toks) * tw + gap * (len(toks) - 1)
        x = (W - tot) / 2
        ty = y + 0.95
        for i, t in enumerate(toks):
            s.box('Token', x + i * (tw + gap), ty, tw, 0.6, [(t, 'h')], pt=17, al='ctr', anchor='ctr', fill='FFFFFF',
                  line=ACC[i % 2], lw=2)
            s.text(str(i + 1), x + i * (tw + gap), ty + 0.62, tw, 0.3, 12, TEAL_D, True, 'ctr')
        s.line(W / 2, y + 0.75, W / 2, ty - 0.04, TEAL_D, 1.5, True)
        cap(s, sp['cap'], ty + 0.95)
    elif L == 'def_diagram':
        dia(s, sp['dia'], X0 + 0.8, y, X1 - X0 - 0.8, bottom - y)
    elif L == 'def_list':
        dia(s, sp['dia'], X0, top, 4.8, bottom - top - 0.5)
        s.text(sp['ex_lab'], X0 + 4.6, y, X1 - X0 - 4.6, 0.36, 15, NAVY, True, 'r')
        its = sp['items']
        for i, t in enumerate(its):
            s.box('Item', X1 - 5.2, y + 0.45 + i * 0.5, 5.2, 0.42, [(t, 'x')], pt=13, al='r', anchor='ctr', fill='FFFFFF',
                  line=TEAL, adj={'adj': 50000}, ins=(0.2, 0, 0.2, 0))
        cap(s, sp['cap'], bottom - 0.4)
    elif L == 'runs':
        runs = sp['runs']
        rw = 3.4
        ry = y + 0.1
        rh = bottom - ry - 0.05
        xs = [W / 2 + 0.55, W / 2 - 0.55 - rw]
        for k, r in enumerate(runs):
            x = xs[k]
            s.rect(x, ry, rw, rh, 'FFFFFF', 'roundRect', {'adj': 7000}, line=TEAL)
            s.box('RunH', x, ry, rw, 0.45, [(r['h'], 'h')], pt=13, al='ctr', anchor='ctr', fill=TEAL, geom='round2SameRect',
                  adj={'adj1': 25000, 'adj2': 0}, hcol='FFFFFF')
            s.box('Prompt', x + 0.25, ry + 0.6, rw - 0.5, 0.42, [(r['p'], 'c')], pt=12, al='ctr', anchor='ctr', fill=SOFT)
            s.line(x + rw / 2, ry + 1.08, x + rw / 2, ry + 1.35, TEAL_D, 1.5, True)
            s.text(r['n'], x, ry + 1.35, rw, 0.7, 36, TEAL_D, True, 'ctr')
            s.text(r['lab'], x, ry + 2.0, rw, 0.35, 13, GRAY, False, 'ctr')
        s.text('≠', W / 2 - 0.4, ry + rh / 2 - 0.4, 0.8, 0.8, 36, ORANGE, True, 'ctr')


def L_list_dia(s, sp, top):
    bottom = note(s, sp.get('note'))
    dw = 4.8
    dia(s, sp['dia'], X0, top, dw, bottom - top)
    items = sp['items']
    x0 = X0 + dw + 0.4
    gap = 0.18
    ih = (bottom - top - gap * (len(items) - 1)) / len(items)
    for k, it in enumerate(items):
        y = top + k * (ih + gap)
        s.rect(x0, y, X1 - x0, ih, 'FFFFFF', 'roundRect', {'adj': 9000}, line=LINE)
        s.rect(X1 - 0.07, y + 0.1, 0.07, ih - 0.2, ACC[k % 3])
        off = 0
        if it.get('ic'):
            s.icon(it['ic'], x0 + 0.2, y + ih / 2 - 0.25, 0.5, 't')
            off = 0.75
        its = []
        if it.get('s') and not it.get('h'):
            its.append((it['s'], 's'))
        if it.get('h'):
            if it.get('s') and it['s'] in ('קלט חזותי', 'קלט טקסטואלי', 'פלט'):
                its.append((it['s'], 's'))
                its.append((it['h'], 'h'))
            else:
                its.append((it['h'], 'h'))
                if it.get('s'):
                    its.append((it['s'], 's'))
        its.append((it['x'], 'x'))
        s.box('Item', x0 + 0.2 + off, y + 0.04, X1 - x0 - 0.45 - off, ih - 0.08, its, 16, 9, al='r', anchor='ctr',
              ins=(0.02, 0, 0.02, 0), spacing=0.3)


def L_hub(s, sp, top):
    bottom = note(s, sp.get('note'))
    if sp.get('cap'):
        bottom -= 0.45
        cap(s, sp['cap'], bottom + 0.08)
    dia(s, sp['dia'], X0 + 2.0, top, X1 - X0 - 4.0, bottom - top)


def L_semantic(s, sp, top):
    bottom = note(s, sp.get('note'), 5.95)
    s.rect(X0 + 0.5, top, X1 - X0 - 1.0, bottom - top, 'FFFFFF', 'roundRect', {'adj': 5000}, line=LINE)
    dia(s, sp['dia'], X0 + 0.7, top + 0.1, X1 - X0 - 1.4, bottom - top - 0.2)


def L_flow_tiles(s, sp, top):
    bottom = note(s, sp.get('note'))
    tiles = sp['tiles']
    th = 1.45
    s.rect(X0, top, X1 - X0, th + 0.55, SOFT, 'roundRect', {'adj': 6000})
    s.text(sp['tiles_h'], X0 + 0.3, top + 0.06, X1 - X0 - 0.6, 0.34, 13, TEAL_D, True, 'r')
    ics = ['image', 'table', 'image', 'window']
    cells = grid(len(tiles), top + 0.42, top + 0.42 + th, len(tiles), X0 + 0.25, X1 - 0.25, 0.25)
    for k, ((a, b), c) in enumerate(zip(tiles, cells)):
        x, y, w, h = c
        s.rect(x, y, w, h - 0.05, 'FFFFFF', 'roundRect', {'adj': 9000}, line=LINE)
        s.icon(ics[k % 4], x + w / 2 - 0.22, y + 0.12, 0.44, 't')
        s.box('Tile', x + 0.1, y + 0.6, w - 0.2, h - 0.7, [(a, 'h'), (b, 'g')], 17, 9, al='ctr', anchor='ctr',
              ins=(0.02, 0, 0.02, 0))
    fl = sp['flow']
    ops = sp['flow_ops']
    fy = top + th + 0.9
    fh = min(1.4, bottom - fy)
    n = len(fl)
    gap = 0.55
    fw = (X1 - X0 - gap * (n - 1)) / n
    for i, (a, b) in enumerate(fl):
        x = X1 - (i + 1) * fw - i * gap
        main = 'LLM' in a
        last = i == n - 1
        s.box('Flow', x, fy, fw, fh, [(a, 'h')] + ([(b, 'g')] if b else []), 18, 9, al='ctr', anchor='ctr',
              fill=TEAL if main else ('FFF6EA' if last else 'FFFFFF'), line=TEAL if not last else ORANGE, lw=1.5,
              hcol='FFFFFF' if main else (OR_D if last else NAVY), col='FFFFFF' if main else GRAY)
        if i < n - 1:
            if ops[i] == '+':
                s.text('+', x - gap, fy + fh / 2 - 0.3, gap, 0.6, 30, ORANGE, True, 'ctr')
            else:
                s.line(x - 0.06, fy + fh / 2, x - gap + 0.06, fy + fh / 2, NAVY, 2, True)


def L_io(s, sp, top):
    bottom = note(s, sp.get('note'))
    gap = 0.9
    cw = (X1 - X0 - 2 * gap) / 3
    cols = [sp['in'], sp['mid'], sp['out']]
    for k, c in enumerate(cols):
        x = X1 - (k + 1) * cw - k * gap
        mid = k == 1
        s.rect(x, top, cw, bottom - top, TINT if mid else 'FFFFFF', 'roundRect', {'adj': 6000}, line=TEAL, lw=1.5 if mid else 1)
        s.box('Head', x, top, cw, 0.55, [(c['h'], 'h')], pt=15, al='ctr', anchor='ctr', fill=TEAL if mid else NAVY,
              geom='round2SameRect', adj={'adj1': 25000, 'adj2': 0}, hcol='FFFFFF')
        if mid:
            s.rect(x + cw / 2 - 0.55, top + 0.95, 1.1, 1.1, NAVY, 'ellipse')
            s.icon('brain', x + cw / 2 - 0.33, top + 1.17, 0.66, 'w')
            s.text(c['x'], x, top + 2.25, cw, 0.4, 15, NAVY, True, 'ctr')
            pills(s, c['pills'], x + 0.15, top + 2.8, cw - 0.3, 0.36, 11, al='ctr')
        else:
            its = c['items']
            ih = (bottom - top - 0.75) / len(its)
            for j, (a, b) in enumerate(its):
                s.box('Item', x + 0.2, top + 0.7 + j * ih, cw - 0.4, ih - 0.1, [(a, 'h'), (b, 'g')], 17, 9, al='r',
                      anchor='ctr', ins=(0.02, 0, 0.02, 0))
    for k, lab in enumerate(sp.get('arrows', [])):
        ax = X1 - (k + 1) * cw - k * gap
        cy = (top + bottom) / 2
        s.line(ax - 0.1, cy, ax - gap + 0.1, cy, ORANGE, 3, True)
        s.text(lab, ax - gap, cy + 0.12, gap, 0.3, 11, OR_D, True, 'ctr')


def L_summary(s, sp, top):
    bottom = 6.78
    if sp.get('cap'):
        bottom -= 0.5
        s.box('Cap', X0, bottom + 0.1, X1 - X0, 0.4, [(sp['cap'], 'x')], pt=13, al='ctr', anchor='ctr', fill=TINT)
    items = sp['items']
    cells = grid(len(items), top, bottom, 2 if len(items) <= 6 else 3)
    for k, (it, c) in enumerate(zip(items, cells)):
        x, y, w, h = c
        s.rect(x, y, w, h, 'FFFFFF', 'roundRect', {'adj': 9000}, line=LINE)
        s.rect(x + w - 0.07, y + 0.1, 0.07, h - 0.2, ACC[k % 3])
        s.box('Sum', x + 0.2, y + 0.05, w - 0.45, h - 0.1, [(it['h'], 's'), (it['x'], 'x')], 16, 9, al='r', anchor='ctr',
              ins=(0.02, 0, 0.02, 0))


def L_exam(s, sp, top):
    gap = 0.5
    cw = (X1 - X0 - gap) / 2
    bottom = note(s, sp.get('note'))
    for k, key in enumerate(('good', 'bad')):
        c = sp[key]
        x = X1 - (k + 1) * cw - k * gap
        good = key == 'good'
        col = GOOD if good else BAD
        its = c['items']
        h = bottom - top if good else min(bottom - top, 0.85 + 0.55 * len(its))
        s.rect(x, top, cw, h, 'FFFFFF', 'roundRect', {'adj': 5000}, line=col, lw=1.5)
        s.box('Head', x, top, cw, 0.6, [(c['h'], 'h')], pt=17, al='ctr', anchor='ctr', fill=col, geom='round2SameRect',
              adj={'adj1': 20000, 'adj2': 0}, hcol='FFFFFF')
        s.box('List', x + 0.3, top + 0.75, cw - 0.6, h - 0.9, [(t, 'k' if good else 'v') for t in its], 17, 10, al='r',
              anchor='t', ins=(0.02, 0, 0.02, 0), spacing=0.6)


def L_exercise(s, sp, top):
    """exercise opener"""
    tags(s, sp, top)
    bottom = 6.78
    meta = sp['meta']
    extra = sp.get('code') or sp.get('items') or sp.get('goal_list')
    mh = 2.2 if not extra else 1.75
    cells = grid(len(meta), top + 0.05, top + mh, 2, X0 + 1.0, X1 - 1.0, 0.25)
    ics = ['users', 'clock', 'book', 'tools']
    for k, ((a, b), c) in enumerate(zip(meta, cells)):
        x, y, w, h = c
        s.rect(x, y, w, h, 'FFFFFF', 'roundRect', {'adj': 9000}, line=LINE)
        s.rect(x + w - 0.07, y + 0.1, 0.07, h - 0.2, ORANGE if k % 2 else TEAL)
        s.icon(ics[k % 4], x + 0.25, y + h / 2 - 0.24, 0.48, 'o' if k % 2 else 't')
        s.box('Meta', x + 0.9, y + 0.04, w - 1.2, h - 0.08, [(a, 'g'), (b, 'h')], 16, 9, al='r', anchor='ctr',
              ins=(0.02, 0, 0.02, 0))
    gy = top + mh + 0.25
    gl = sp.get('goal_list')
    gh = 1.0 if not gl else 0.45 + 0.36 * len(gl)
    s.rect(X0 + 1.0, gy, X1 - X0 - 2.0, gh, 'FFF6EA', 'roundRect', {'adj': 12000})
    s.icon('target', X0 + 1.25, gy + gh / 2 - 0.25, 0.5, 'o')
    lab = sp.get('goal_lab', 'מטרה')
    if gl:
        items = [(lab, 'o')] + [(t, 'b') for t in gl]
    else:
        items = [(f"**{lab}:** {sp['goal']}", 'x')]
    s.box('Goal', X0 + 2.0, gy + 0.04, X1 - X0 - 3.3, gh - 0.08, items, 17, 10, al='r', anchor='ctr',
          ins=(0.02, 0, 0.02, 0), bcol=ORANGE)
    y = gy + gh + 0.2
    if sp.get('goal_pills'):
        pills(s, sp['goal_pills'], X0 + 1.0, y, X1 - X0 - 2.0, 0.38, 13, fill='FFF6EA', col=OR_D, al='ctr')
        y += 0.55
    if sp.get('items'):
        if sp.get('items_h'):
            s.text(sp['items_h'], X0 + 1.0, y, X1 - X0 - 2.0, 0.3, 13, TEAL_D, True, 'r')
            y += 0.35
        pills(s, sp['items'], X0 + 1.0, y, X1 - X0 - 2.0, 0.4, 13, al='ctr')
        y += 0.6 if len(sp['items']) < 5 else 0.7
    if sp.get('code'):
        ch = min(1.35, bottom - 0.65 - y)
        code_panel(s, X0 + 1.0, y, X1 - X0 - 2.0, ch, sp['code'], '', 14)
        y += ch + 0.12
    exbtn(s, sp, min(y + 0.05, bottom - 0.5))


def exbtn(s, sp, y):
    if not sp.get('ex'):
        return
    lab = f"לפתיחת התרגיל {sp['ex']} ←"
    w = wlen(lab, 14, 1) + 0.7
    s.box('Exercise Link', (W - w) / 2, y, w, 0.48, [(lab, 'h')], pt=14, al='ctr', anchor='ctr', fill=ORANGE,
          adj={'adj': 50000}, hcol='FFFFFF')
    s.links.append({'ex': sp['ex'], 'x': round((W - w) / 2 / W * 100, 2), 'y': round(y / H * 100, 2),
                    'w': round(w / W * 100, 2), 'h': round(0.48 / H * 100, 2)})


def tags(s, sp, top):
    t = sp.get('tags')
    if t:
        pills(s, t, X0 + (2.0 if sp.get('ex') else 0), 0.92, 5.0, 0.32, 11, fill='FFF6EA', col=OR_D, al='l')


def L_ex_steps(s, sp, top):
    tags(s, sp, top)
    bottom = 6.78
    steps = sp['steps']
    sw = 6.4
    x0 = X1 - sw
    gap = 0.16
    sh = (bottom - top - gap * (len(steps) - 1)) / len(steps)
    for i, st in enumerate(steps):
        y = top + i * (sh + gap)
        s.rect(x0, y, sw, sh, 'FFFFFF', 'roundRect', {'adj': 9000}, line=LINE)
        s.text(str(i + 1), X1 - 0.7, y, 0.6, sh, 28, ORANGE, True, 'ctr')
        s.box('Step', x0 + 0.2, y + 0.04, sw - 1.0, sh - 0.08, [(st, 'x')], 17, 9, al='r', anchor='ctr',
              ins=(0.02, 0, 0.02, 0))
    side = sp.get('side', [])
    x1 = x0 - 0.35
    sy = top
    hs = []
    for b in side:
        hs.append(1.0 + 0.45 * len(b.get('items', [])) + (0.9 if b.get('fill') else 0))
    sc = (bottom - top - 0.2 * (len(side) - 1)) / max(0.1, sum(hs))
    for b, hh in zip(side, hs):
        hh *= sc
        s.rect(X0, sy, x1 - X0, hh, SOFT, 'roundRect', {'adj': 7000}, line=LINE)
        items = [(b['h'], 'o')]
        if b.get('x'):
            items.append((b['x'], 'h'))
        for it in b.get('items', []):
            items.append((it, 'b'))
        th = hh - (0.95 if b.get('fill') else 0.1)
        s.box('Side', X0 + 0.2, sy + 0.08, x1 - X0 - 0.4, th, items, 16, 9, al='r', anchor='t', ins=(0.02, 0, 0.02, 0))
        if b.get('fill'):
            fw = 1.2
            for j, f in enumerate(b['fill']):
                fx = x1 - 0.3 - (j + 1) * fw - j * 0.2
                s.text(f, fx, sy + hh - 0.85, fw, 0.3, 11, GRAY, False, 'ctr')
                s.rect(fx, sy + hh - 0.52, fw, 0.4, 'FFFFFF', 'roundRect', line='B9C4D6', dash='dash')
        sy += hh + 0.2


def L_ex_table(s, sp, top):
    tags(s, sp, top)
    if sp.get('lead'):
        s.box('Lead', X0, top, X1 - X0, 0.5, [(sp['lead'], 'x')], pt=13, al='r', anchor='ctr', fill='FFF6EA',
              ins=(0.25, 0, 0.25, 0))
        top += 0.7
    L_table(s, sp, top, qs=sp.get('qs'))


def L_ex_compare(s, sp, top):
    tags(s, sp, top)
    bottom = note(s, sp.get('note'), 6.0)
    cols = sp['cols']
    ch_h = 1.6
    gap = 0.8
    cw = (X1 - X0 - gap) / 2
    for k, c in enumerate(cols):
        x = X1 - (k + 1) * cw - k * gap
        s.rect(x, top, cw, ch_h, 'FFFFFF', 'roundRect', {'adj': 8000}, line=LINE)
        s.text(c['h'], x + 0.2, top + 0.05, cw - 0.4, 0.35, 14, OR_D, True, 'r')
        s.box('Code', x + 0.2, top + 0.42, cw - 0.4, 0.72, [(c['code'], 'x')], 13, 9, al='r', anchor='ctr', fill=NAVY,
              col='FFFFFF', ins=(0.15, 0.04, 0.15, 0.04))
        pills(s, c['tags'], x + 0.2, top + 1.2, cw - 0.4, 0.32, 11)
    s.text('VS', X0 + cw, top + ch_h / 2 - 0.3, gap, 0.6, 22, ORANGE, True, 'ctr')
    c = sp['challenge']
    y = top + ch_h + 0.25
    hh = bottom - y
    s.rect(X0, y, X1 - X0, hh, 'FFF6EA', 'roundRect', {'adj': 7000})
    s.rect(X1 - 0.08, y + 0.1, 0.08, hh - 0.2, ORANGE)
    s.box('Ch', X0 + 0.3, y + 0.05, X1 - X0 - 0.6, 0.85, [(c['h'], 'h'), (c['x'], 'x')], 17, 10, al='r', anchor='t',
          ins=(0.02, 0, 0.02, 0))
    pills(s, c['pills'], X0 + 0.3, y + 0.95, X1 - X0 - 0.6, 0.38, 13, fill='FFFFFF', line=ORANGE, col=OR_D)
    s.text(c['x2'], X0 + 0.3, y + 1.4, X1 - X0 - 0.6, 0.35, 14, NAVY, True, 'r')


def L_rows(s, sp, top):
    bottom = note(s, sp.get('note'))
    rows = sp['rows']
    gap = 0.12
    rh = (bottom - top - gap * (len(rows) - 1)) / len(rows)
    lw = 2.4
    for k, (a, b, c) in enumerate(rows):
        y = top + k * (rh + gap)
        acc = [TEAL, TEAL_D, '7FD8D2', '5B6BB5', ORANGE, TEAL][k % 6]
        s.rect(X0, y, X1 - X0, rh, 'FFFFFF', 'roundRect', {'adj': 12000}, line=LINE)
        s.rect(X1 - 0.08, y, 0.08, rh, acc)
        s.box('Num', X1 - 0.55, y + rh / 2 - 0.19, 0.38, 0.38, [(str(k + 1), 'h')], pt=12, al='ctr', anchor='ctr',
              fill=acc, geom='ellipse', hcol='FFFFFF', ins=(0, 0, 0, 0))
        s.box('Label', X1 - 0.65 - lw, y, lw, rh, [(a, 'h'), (b, 'g')], 16, 9, al='r', anchor='ctr', ins=(0.02, 0, 0.02, 0),
              spacing=0.1)
        s.box('Value', X0 + 0.2, y, X1 - X0 - lw - 1.1, rh, [(c, 'x')], 16, 9, al='r' if sp.get('rtl_val') else 'l', anchor='ctr',
              ins=(0.02, 0, 0.02, 0))


def L_code_steps(s, sp, top):
    tags(s, sp, top)
    bottom = note(s, sp.get('note'))
    steps = sp['steps']
    wts = [1.4 + st['code'].count('\n') * 0.3 + len(st['code']) / 300 for st in steps]
    gap = 0.2
    avail = bottom - top - gap * (len(steps) - 1)
    y = top
    for k, (st, wt) in enumerate(zip(steps, wts)):
        h = avail * wt / sum(wts)
        s.box('Num', X1 - 0.5, y + 0.05, 0.45, 0.45, [(str(k + 1), 'h')], pt=15, al='ctr', anchor='ctr', fill=ORANGE,
              geom='ellipse', hcol='FFFFFF', ins=(0, 0, 0, 0))
        s.text(st['h'], X0 + 3.0, y, X1 - X0 - 3.65, 0.36, 14, NAVY, True, 'r')
        ch = h - 0.42
        ow = 2.6 if st.get('out') else 0
        code_panel(s, X0 + ow, y + 0.4, X1 - X0 - 0.65 - ow, ch, st['code'], '', 14)
        if st.get('out'):
            s.box('Out', X0, y + 0.4 + ch / 2 - 0.22, ow - 0.15, 0.44, [(st['out'], 'k')], pt=11, al='ctr',
                  anchor='ctr', fill=TINT, col=TEAL_D, adj={'adj': 50000}, ins=(0.04, 0, 0.04, 0))
        y += h + gap


def L_code_flow(s, sp, top):
    bottom = note(s, sp.get('note'))
    cols = sp['cols']
    n = len(cols)
    gap = 0.55
    cw = (X1 - X0 - gap * (n - 1)) / n
    for k, c in enumerate(cols):
        x = X1 - (k + 1) * cw - k * gap
        main, out = c.get('main'), c.get('out')
        col = ORANGE if (main or out) else TEAL
        h = bottom - top - (0.4 if c.get('g') else 0)
        s.rect(x, top, cw, h, 'FFFFFF', 'roundRect', {'adj': 6000}, line=col, lw=1.5)
        s.box('Head', x + 0.1, top + 0.05, cw - 0.2, 0.75, [(c['h'], 'h'), (c['s'], 's')], 15, 9, al='ctr', anchor='ctr',
              ins=(0.02, 0, 0.02, 0), hcol=OR_D if (main or out) else NAVY)
        code_panel(s, x + 0.12, top + 0.85, cw - 0.24, h - 0.97, c['code'], '', 13)
        if c.get('g'):
            s.text(c['g'], x, top + h + 0.05, cw, 0.3, 10.5, GRAY, False, 'ctr')
        if k < n - 1:
            cy = top + h / 2
            s.line(x - 0.05, cy, x - gap + 0.05, cy, NAVY, 2, True)
            if sp.get('arrows'):
                s.box('Arrow Lab', x - gap - 0.05, cy - 0.75, gap + 0.1, 0.6, [(sp['arrows'][k], 'g')], 10, 7, al='ctr',
                      anchor='b', ins=(0, 0, 0, 0))


def L_loop(s, sp, top):
    bottom = note(s, sp.get('note'))
    pills_h = 0.9 if sp.get('pills') else 0
    cy = (top + bottom - pills_h) / 2
    bw, bh = 2.6, 1.5
    ax = X1 - 2.2 - bw
    bx = X0 + 2.2
    for (x, (a, b), col) in ((ax, sp['a'], ORANGE), (bx, sp['b'], TEAL)):
        s.box('Node', x, cy - bh / 2, bw, bh, [(a, 't'), (b, 'g')], 22, 10, al='ctr', anchor='ctr', fill='FFFFFF',
              line=col, lw=2)
    s.icon('user', ax + bw / 2 - 0.25, cy - bh / 2 - 0.62, 0.5, 'o')
    s.icon('brain', bx + bw / 2 - 0.25, cy - bh / 2 - 0.62, 0.5, 't')
    # top arrow a->b, bottom arrow b->a
    s.line(ax - 0.1, cy - 0.35, bx + bw + 0.1, cy - 0.35, TEAL_D, 2.5, True)
    s.line(bx + bw + 0.1, cy + 0.35, ax - 0.1, cy + 0.35, ORANGE, 2.5, True)
    mx, mw = bx + bw + 0.1, ax - bx - bw - 0.2
    s.box('AB', mx, cy - 1.15, mw, 0.7, [(sp['ab'][0], 'h'), (sp['ab'][1], 'g')], 16, 9, al='ctr', anchor='b',
          ins=(0, 0, 0, 0))
    s.box('BA', mx, cy + 0.45, mw, 0.7, [(sp['ba'][0], 'h'), (sp['ba'][1], 'g')], 16, 9, al='ctr', anchor='t',
          ins=(0, 0, 0, 0))
    if sp.get('pills'):
        ps = sp['pills']
        pw = 2.9
        tot = pw * len(ps) + 0.3 * (len(ps) - 1)
        x = (W + tot) / 2
        for a, b in ps:
            x -= pw
            s.box('Pill', x, bottom - 0.75, pw, 0.68, [(a, 'h'), (b, 'g')], 14, 8, al='ctr', anchor='ctr', fill=TINT,
                  adj={'adj': 50000}, ins=(0.05, 0, 0.05, 0), spacing=0.1)
            x -= 0.3


def L_qlist(s, sp, top):
    bottom = note(s, sp.get('note'))
    its = sp['items']
    gap = 0.16
    rh = min(0.95, (bottom - top - gap * (len(its) - 1)) / len(its))
    y = top + (bottom - top - rh * len(its) - gap * (len(its) - 1)) / 2
    for k, q in enumerate(its):
        s.rect(X0 + 1.0, y, X1 - X0 - 1.0, rh, 'FFFFFF', 'roundRect', {'adj': 15000}, line=LINE)
        s.text(f'{k + 1:02d}', X1 - 1.0, y, 0.85, rh, 28, TEAL_D, True, 'ctr')
        s.box('Q', X0 + 1.2, y, X1 - X0 - 2.4, rh, [(q, 'x')], 20, 11, al='r', anchor='ctr', ins=(0.02, 0, 0.02, 0))
        y += rh + gap
    s.rect(X0, top + (bottom - top) / 2 - 0.45, 0.9, 0.9, TINT, 'ellipse')
    s.icon('question', X0 + 0.2, top + (bottom - top) / 2 - 0.25, 0.5, 't')


def L_runs3(s, sp, top):
    bottom = note(s, sp.get('note'))
    cx = X1 - 3.0
    cy = (top + bottom) / 2 - 0.3
    s.box('Src', cx - 1.3, cy - 0.5, 2.6, 1.0, [(sp['src'][0], 't'), (sp['src'][1], 's')], 22, 10, al='ctr', anchor='ctr',
          fill='FFFFFF', line=TEAL, lw=2)
    outs = sp['outs']
    bx = X0 + 4.0
    bw = 3.0
    oh = (bottom - top - 0.9) / len(outs)
    s.text(sp.get('cap', ''), bx - 0.5, top, bw + 1, 0.32, 12, TEAL_D, True, 'ctr')
    for k, o in enumerate(outs):
        oy = top + 0.45 + k * oh
        s.box('Out', bx, oy, bw, oh - 0.2, [(o, 'h')], pt=16, al='r', anchor='ctr', fill=NAVY, hcol='FFFFFF',
              geom='wedgeRoundRectCallout', adj={'adj1': -40000, 'adj2': 30000, 'adj3': 16667}, ins=(0.2, 0, 0.25, 0))
        s.line(cx - 1.35, cy, bx + bw + 0.1, oy + (oh - 0.2) / 2, NAVY, 1.5, True)
    s.box('X', X0, bottom - 1.0, 3.6, 0.9, [(t, 'x') for t in sp.get('x', [])], 15, 9, al='r', anchor='ctr',
          ins=(0.02, 0, 0.02, 0))


def L_exam_one(s, sp, top):
    bottom = 6.78
    if sp.get('cap'):
        bottom -= 0.5
        s.box('Cap', X0, bottom + 0.1, X1 - X0, 0.4, [(sp['cap'], 'h')], pt=14, al='ctr', anchor='ctr', fill=TINT, hcol=TEAL_D)
    its = sp['items']
    gap = 0.14
    rh = min(0.8, (bottom - top - gap * (len(its) - 1)) / len(its))
    y = top
    for k, t in enumerate(its):
        s.rect(X0 + 1.4, y, X1 - X0 - 1.4, rh, TINT if k % 2 == 0 else 'EEF0FA', 'roundRect', {'adj': 15000})
        s.rect(X1 - 0.07, y, 0.07, rh, TEAL)
        s.rect(X1 - 0.75, y + rh / 2 - 0.25, 0.5, 0.5, NAVY, 'ellipse')
        s.icon('check', X1 - 0.65, y + rh / 2 - 0.15, 0.3, 'w')
        s.box('Item', X0 + 1.6, y, X1 - X0 - 2.55, rh, [(t, 'h')], 18, 10, al='r', anchor='ctr', ins=(0.02, 0, 0.02, 0))
        y += rh + gap
    s.icon('grad', X0 + 0.1, top + 0.1, 1.1, 't')


def L_bars(s, sp, top):
    bottom = note(s, sp.get('note'))
    if sp.get('lead'):
        ld = sp['lead']
        s.box('Lead', X0, top, X1 - X0, 0.85, [(ld['x'], 'x'), (ld.get('g', ''), 'g')], 16, 9, al='r', anchor='ctr',
              fill=TINT, ins=(0.25, 0.04, 0.25, 0.04))
        top += 1.05
    rows = sp['rows']
    gap = 0.2
    rh = min(1.1, (bottom - top - gap * (len(rows) - 1)) / len(rows))
    for k, (a, b, lab, v, col) in enumerate(rows):
        y = top + k * (rh + gap)
        s.rect(X0, y, X1 - X0, rh, 'FFFFFF', 'roundRect', {'adj': 12000}, line=LINE)
        s.rect(X1 - 0.08, y, 0.08, rh, col)
        s.box('Name', X1 - 3.6, y, 3.4, rh, [(a, 'h'), (b, 'g')], 17, 9, al='r', anchor='ctr', ins=(0.02, 0, 0.02, 0))
        bx0, bx1 = X0 + 2.6, X1 - 3.9
        s.rect(bx0, y + rh / 2 - 0.07, bx1 - bx0, 0.14, SOFT, 'roundRect', {'adj': 50000})
        w = (bx1 - bx0) * v
        s.rect(bx1 - w, y + rh / 2 - 0.07, w, 0.14, col, 'roundRect', {'adj': 50000})
        s.rect(bx1 - w - 0.13, y + rh / 2 - 0.13, 0.26, 0.26, 'FFFFFF', 'ellipse', line=col, lw=2.5)
        s.box('Stage', X0 + 0.15, y + rh / 2 - 0.27, 2.25, 0.54, [(lab, 'k')], pt=11, al='ctr', anchor='ctr', fill=col,
              col='FFFFFF', adj={'adj': 50000}, ins=(0.04, 0, 0.04, 0))


def L_venn(s, sp, top):
    bottom = note(s, sp.get('note'))
    cx, cy = X0 + 4.6, (top + bottom) / 2 + 0.05
    r = min(1.55, (bottom - top) / 3.1)
    pos = [(cx + r * 0.62, cy - r * 0.42), (cx - r * 0.62, cy - r * 0.42), (cx, cy + r * 0.6)]
    for (px, py), (a, b, col) in zip(pos, sp['circles']):
        s.rect(px - r, py - r, 2 * r, 2 * r, col, 'ellipse', alpha=30000, line=col, lw=1.5)
    lp = [(cx + r * 1.05, cy - r * 0.75), (cx - r * 1.05, cy - r * 0.75), (cx, cy + r * 1.05)]
    for (px, py), (a, b, col) in zip(lp, sp['circles']):
        s.box('Circle', px - 1.15, py - 0.42, 2.3, 0.84, [(a, 'h'), (b, 'g')], 15, 9, al='ctr', anchor='ctr', ins=(0, 0, 0, 0))
    s.box('Center', cx - 0.85, cy - 0.32, 1.7, 0.6, [(sp['center'][0], 'h'), (sp['center'][1], 'g')], 13, 8, al='ctr',
          anchor='ctr', fill=NAVY, hcol='FFFFFF', col='C9CBF0', adj={'adj': 30000}, ins=(0.02, 0, 0.02, 0))
    sx = X0 + 9.0
    for k, (a, b) in enumerate(sp.get('side', [])):
        s.box('Side', sx, top + 0.8 + k * 1.5, X1 - sx, 1.1, [(a, 'h'), (b, 's')], 20, 10, al='ctr', anchor='ctr',
              fill='FFFFFF', line=ORANGE if k == 0 else TEAL, lw=1.5, adj={'adj': 50000})


LAY = {'cards': L_cards, 'blocks': L_blocks, 'steps': L_steps, 'table': L_table, 'vs': L_vs, 'proscons': L_proscons,
       'timeline': L_timeline, 'code_side': L_code_side, 'def_tiles': L_def_x, 'tokens': L_def_x, 'def_diagram': L_def_x,
       'def_list': L_def_x, 'runs': L_def_x, 'list_dia': L_list_dia, 'hub': L_hub, 'semantic': L_semantic,
       'flow_tiles': L_flow_tiles, 'io': L_io, 'summary': L_summary, 'exam': L_exam, 'exercise': L_exercise,
       'ex_steps': L_ex_steps, 'rows': L_rows, 'code_steps': L_code_steps, 'code_flow': L_code_flow, 'loop': L_loop, 'qlist': L_qlist, 'exam_one': L_exam_one, 'bars': L_bars, 'venn': L_venn, 'runs3': L_runs3, 'ex_table': L_ex_table, 'ex_compare': L_ex_compare}


def build(sp):
    s = Slide()
    L = sp['L']
    if L == 'cover':
        L_cover(s, sp)
    elif L == 'section':
        L_section(s, sp)
    else:
        if L == 'cards' and sp.get('sub') and len(sp['sub']) <= 4:
            sp['mid'] = sp.pop('sub')
        top = title(s, sp)
        LAY[L](s, sp, top)
        if L not in ('exercise', 'ex_steps', 'ex_table', 'ex_compare', 'code_steps'):
            tags(s, sp, top)
        if sp.get('ex') and L not in ('exercise',):
            # small link button in the title area (left of the title)
            lab = f"לתרגיל {sp['ex']} ←"
            w = wlen(lab, 11, 1) + 0.5
            s.box('Exercise Link', X0, 0.92, w, 0.32,
                  [(lab, 'h')], pt=11, al='ctr', anchor='ctr', fill=ORANGE, adj={'adj': 50000}, hcol='FFFFFF',
                  ins=(0.02, 0, 0.02, 0))
            yy = 0.92
            s.links.append({'ex': sp['ex'], 'x': round(X0 / W * 100, 2), 'y': round(yy / H * 100, 2),
                            'w': round(w / W * 100, 2), 'h': round(0.34 / H * 100, 2)})
    return s


# ---------------------------------------------------------------- TOC
def toc_entries(specs):
    """first slide of every numbered section (from kicker)"""
    ents = []
    seen = set()
    for idx, sp in enumerate(specs, 1):
        if sp['L'] == 'cover':
            continue
        k = sp.get('k') or ''
        m = re.match(r'^(\d+(?:\.\d+)*)', k.strip())
        if not m:
            continue
        num = m.group(1)
        if num in seen:
            continue
        seen.add(num)
        lvl = num.count('.')
        ents.append((lvl, num, sp.get('toc') or sp['t'], idx))
    return ents


def toc_slide(specs, ents):
    s = Slide()
    s.text(f'תוכן עניינים · פרק {N}: {CHAPTER[N]}', TX0, 0.28, X1 - TX0, 0.6, 26, NAVY, True, 'r', name='TOC Title')
    s.text('לחיצה על נושא עוברת לשקף הראשון שלו', TX0, 0.86, X1 - TX0, 0.3, 12, GRAY, False, 'r')
    top, bottom = 1.35, 6.75
    cols = 1 if len(ents) <= 11 else 2
    if cols == 2:
        half = (len(ents) + 1) // 2
        groups = [ents[:half], ents[half:]]
    else:
        groups = [ents]
    rows = max(len(g) for g in groups)
    rh = min(0.46, (bottom - top) / rows)
    cw = (X1 - X0 - 0.4) / 2 if cols == 2 else 8.6
    for ci, g in enumerate(groups):
        right = X1 - ci * (cw + 0.4) if cols == 2 else (W + cw) / 2
        for ri, (lvl, num, lab, idx) in enumerate(g):
            y = top + ri * rh
            ind = 0.35 * min(lvl, 2)
            w = cw - ind
            x = right - w
            main = lvl <= 1
            rid = f'rId{len(s.rels) + 10}'
            s.rels.append((rid, 'slide', f'@{idx}'))
            fs = 15 if main else 13
            body = (f'<a:p><a:pPr algn="r" rtl="1"/>{run(num + "   ", fs, TEAL_D, True)}'
                    f'{run(lab, fs, NAVY if main else BODY, main)}</a:p>')
            sid = s.ids()
            s.add(f'<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                  f'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                  f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                  f'<p:nvSpPr><p:cNvPr id="{sid}" name="TOC Entry"><a:hlinkClick r:id="{rid}" action="ppaction://hlinksldjump"/></p:cNvPr>'
                  f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y + rh * 0.08)}"/>'
                  f'<a:ext cx="{emu(w)}" cy="{emu(rh * 0.84)}"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>'
                  f'{solid(TINT if main else "FFFFFF")}<a:ln w="9525">{solid(LINE)}</a:ln></p:spPr>'
                  f'<p:txBody><a:bodyPr lIns="91440" rIns="137160" tIns="0" bIns="0" anchor="ctr"><a:normAutofit/></a:bodyPr>'
                  f'<a:lstStyle/>{body}</p:txBody></p:sp>')
            LINKS_TOC.append({'slide': idx + 1, 'x': round(x / W * 100, 2), 'y': round((y + rh * 0.08) / H * 100, 2),
                              'w': round(w / W * 100, 2), 'h': round(rh * 0.84 / H * 100, 2)})
    return s


LINKS_TOC = []


# ---------------------------------------------------------------- package
def main():
    specs = [json.loads(l) for l in open(SPEC) if l.strip()]
    specs.sort(key=lambda d: d['i'])
    ents = toc_entries(specs)
    slides = [build(sp) for sp in specs]
    toc = toc_slide(specs, ents)
    order = [slides[0], toc] + slides[1:]
    # map spec index -> final slide number (cover=1, toc=2)
    final_no = {1: 1}
    for j in range(2, len(specs) + 1):
        final_no[j] = j + 1
    work = tempfile.mkdtemp()
    with zipfile.ZipFile(TPL) as z:
        z.extractall(work)
    sd = os.path.join(work, 'ppt/slides')
    shutil.rmtree(sd)
    os.makedirs(sd + '/_rels')
    if os.path.exists(os.path.join(work, 'ppt/notesSlides')):
        shutil.rmtree(os.path.join(work, 'ppt/notesSlides'))
    md = os.path.join(work, 'ppt/media')
    for f, p in MEDIA.items():
        shutil.copy(p, os.path.join(md, 'g_' + f))
    tot = len(order)
    NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
    site = {'toc': [], 'ex': {}, 'total': tot}
    for i, s in enumerate(order, 1):
        col = 'A9B1C2' if s.dark else '7C7B98'
        rp = (f'<a:rPr lang="en-US" sz="1000" b="1" dirty="0"><a:solidFill><a:srgbClr val="{col}"/></a:solidFill>'
              f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr>')
        counter = (f'<p:sp><p:nvSpPr><p:cNvPr id="{s.ids()}" name="Slide Counter"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                   f'<p:spPr><a:xfrm><a:off x="{emu(0.3)}" y="{emu(7.1)}"/><a:ext cx="{emu(1.1)}" cy="{emu(0.28)}"/></a:xfrm>'
                   f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="none" lIns="0" '
                   f'tIns="0" rIns="0" bIns="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="l" rtl="0"/>'
                   f'<a:fld id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">{rp}<a:t>{i}</a:t></a:fld>'
                   f'<a:r>{rp}<a:t>/{tot}</a:t></a:r></a:p></p:txBody></p:sp>')
        body = ''.join(re.sub(r' xmlns:(p|a|r)="[^"]+"', '', x) for x in s.xml) + counter
        xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<p:sld {NS}><p:cSld><p:spTree>'
               f'<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
               f'<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{body}</p:spTree></p:cSld>'
               f'<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
        open(f'{sd}/slide{i}.xml', 'w', encoding='utf-8').write(xml)
        rels = [f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
                f'Target="../slideLayouts/slideLayout{s.layout}.xml"/>']
        for rid, ty, tg in s.rels:
            if ty == 'slide':
                tg = f'slide{final_no[int(tg[1:])]}.xml'
            rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/{ty}" '
                        f'Target="{tg}"/>')
        open(f'{sd}/_rels/slide{i}.xml.rels', 'w', encoding='utf-8').write(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships '
            'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + ''.join(rels) + '</Relationships>')
        for L in s.links:
            site['ex'].setdefault(L['ex'], []).append(dict(L, slide=i))
    # presentation.xml
    pp = os.path.join(work, 'ppt/presentation.xml')
    pres = open(pp, encoding='utf-8').read()
    prel_p = os.path.join(work, 'ppt/_rels/presentation.xml.rels')
    prel = open(prel_p, encoding='utf-8').read()
    prel = re.sub(r'<Relationship [^>]*Target="slides/slide\d+\.xml"/>', '', prel)
    ids = ''
    for i in range(1, tot + 1):
        prel = prel.replace('</Relationships>', f'<Relationship Id="rIdS{i}" Type="http://schemas.openxmlformats.org/'
                            f'officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/></Relationships>')
        ids += f'<p:sldId id="{256 + i}" r:id="rIdS{i}"/>'
    pres = re.sub(r'<p:sldIdLst>.*?</p:sldIdLst>', f'<p:sldIdLst>{ids}</p:sldIdLst>', pres, flags=re.S)
    pres = re.sub(r'<p:custShowLst>.*?</p:custShowLst>', '', pres, flags=re.S)
    pres = re.sub(r'<p:extLst>.*?</p:extLst>', '', pres, flags=re.S)  # sections
    open(pp, 'w', encoding='utf-8').write(pres)
    open(prel_p, 'w', encoding='utf-8').write(prel)
    # content types
    ctp = os.path.join(work, '[Content_Types].xml')
    ct = open(ctp, encoding='utf-8').read()
    ct = re.sub(r'<Override PartName="/ppt/(slides|notesSlides)/[^"]+"[^>]*/>', '', ct)
    ov = ''.join(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                 f'presentationml.slide+xml"/>' for i in range(1, tot + 1))
    ct = ct.replace('</Types>', ov + '</Types>')
    if 'Extension="png"' not in ct:
        ct = ct.replace('<Default ', '<Default Extension="png" ContentType="image/png"/><Default ', 1)
    open(ctp, 'w', encoding='utf-8').write(ct)
    # master "back to contents" -> slide2
    for mf in os.listdir(os.path.join(work, 'ppt/slideMasters/_rels')):
        p = os.path.join(work, 'ppt/slideMasters/_rels', mf)
        r = open(p, encoding='utf-8').read()
        r = re.sub(r'Target="\.\./slides/slide\d+\.xml"', 'Target="../slides/slide2.xml"', r)
        open(p, 'w', encoding='utf-8').write(r)
    # drop doc props that list old slide titles
    app = os.path.join(work, 'docProps/app.xml')
    if os.path.exists(app):
        a = open(app, encoding='utf-8').read()
        a = re.sub(r'<Slides>\d+</Slides>', f'<Slides>{tot}</Slides>', a)
        a = re.sub(r'<Notes>\d+</Notes>', '<Notes>0</Notes>', a)
        a = re.sub(r'<HeadingPairs>.*?</HeadingPairs>', '', a, flags=re.S)
        a = re.sub(r'<TitlesOfParts>.*?</TitlesOfParts>', '', a, flags=re.S)
        open(app, 'w', encoding='utf-8').write(a)
    core = os.path.join(work, 'docProps/core.xml')
    if os.path.exists(core):
        c = open(core, encoding='utf-8').read()
        c = re.sub(r'<dc:title>.*?</dc:title>', f'<dc:title>CT-GenAI · פרק {N}</dc:title>', c)
        open(core, 'w', encoding='utf-8').write(c)
    o = os.path.abspath(DST)
    if os.path.exists(o):
        os.remove(o)
    os.system(f'cd "{work}" && zip -qXrDy "{o}" .')
    shutil.rmtree(work)
    site['toc'] = [{'lvl': l, 'num': n, 'label': lab, 'slide': final_no[idx]} for l, n, lab, idx in ents]
    site['toc_links'] = LINKS_TOC
    json.dump(site, open(DST.replace('.pptx', '.site.json'), 'w'), ensure_ascii=False)
    print('built', DST, tot, 'slides')


main()
