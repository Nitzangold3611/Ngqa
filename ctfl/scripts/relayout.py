#!/usr/bin/env python3
"""v2 redesign: new title treatment, varied text layouts, new illustrations.
usage: relayout.py N in.pptx out.pptx"""
import sys, os, re, zipfile, copy, json, io
from lxml import etree
from PIL import Image
from lay import *
from extract import classify, order, box, text, kind, maxsz, NUMRE
from topics import topic_for
import redraw

N = int(sys.argv[1]); SRC = sys.argv[2]; DST = sys.argv[3]
ILL = 'assets/illus'
CONTENT = set(json.load(open('content_pics.json')))

z = zipfile.ZipFile(SRC)
parts = {n: z.read(n) for n in z.namelist()}
slides = order(z)
pres = parts['ppt/presentation.xml'].decode()
W = int(re.search(r'sldSz cx="(\d+)"', pres).group(1)) / E
H = int(re.search(r'sldSz[^>]*cy="(\d+)"', pres).group(1)) / E
WIDE = W > 11
# content region
if WIDE:
    X0, X1, Y0, Y1 = 0.55, 12.8, 1.28, 6.82
    TX0 = 1.95
else:
    X0, X1, Y0, Y1 = 0.4, 9.6, 1.2, 6.85
    TX0 = 1.5
TITLE_Y = 0.24 if WIDE else 0.12

# new background
for n in list(parts):
    if n.endswith('ngqa_bg_light.png') or n.endswith('ngqa_bg_light43.png'):
        parts[n] = open('assets/bg_v2.png' if WIDE else 'assets/bg_v2_43.png', 'rb').read()

media_added = {}
CT = parts['[Content_Types].xml'].decode()
if 'Extension="png"' not in CT:
    CT = CT.replace('<Default ', '<Default Extension="png" ContentType="image/png"/><Default ', 1)
parts['[Content_Types].xml'] = CT.encode()


def rels_name(s):
    return 'ppt/' + s.replace('slides/', 'slides/_rels/') + '.rels'


def add_media(slide, path):
    key = os.path.basename(path)
    mname = 'ppt/media/v2_' + key
    if mname not in parts:
        parts[mname] = open(path, 'rb').read() if isinstance(path, str) and os.path.exists(path) else path
    rn = rels_name(slide)
    rel = parts[rn].decode()
    tgt = '../media/v2_' + key
    m = re.search(r'Id="([^"]+)"[^>]*Target="%s"' % re.escape(tgt), rel) or re.search(r'Target="%s"[^>]*Id="([^"]+)"' % re.escape(tgt), rel)
    if m:
        return m.group(1)
    ids = [int(x) for x in re.findall(r'Id="rId(\d+)"', rel)] or [0]
    rid = 'rId%d' % (max(ids) + 1)
    rel = rel.replace('</Relationships>', f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{tgt}"/></Relationships>')
    parts[rn] = rel.encode()
    return rid


def add_media_bytes(slide, name, data):
    mname = 'ppt/media/v2_' + name
    parts[mname] = data
    return add_media(slide, mname)


# ---------------- paragraph model ----------------
def color_of(rpr):
    if rpr is None:
        return None
    f = rpr.find(A + 'solidFill')
    if f is None:
        return None
    c = f.find(A + 'srgbClr')
    if c is not None:
        return c.get('val')
    c = f.find(A + 'schemeClr')
    if c is not None:
        return 'scheme:' + c.get('val')
    return None


def is_emph_color(c):
    if not c:
        return False
    if c.startswith('scheme:'):
        return c[7:] in ('accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6', 'hlink')
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 40:
        return False
    if (r, g, b) == (0x12, 0x11, 0x33) or (r, g, b) == (0x23, 0x22, 0x4A):
        return False
    if mx > 235 and mn > 200:
        return False
    return True


def para_model(p, base_sz, phbody=False):
    ppr = p.find(A + 'pPr')
    lvl = int(ppr.get('lvl', 0)) if ppr is not None else 0
    bullet = None
    if ppr is not None:
        if ppr.find(A + 'buAutoNum') is not None:
            bullet = 'num'
        elif ppr.find(A + 'buChar') is not None:
            bullet = 'char'
        elif ppr.find(A + 'buNone') is not None:
            bullet = None
        elif phbody:
            bullet = 'char'
    elif phbody:
        bullet = 'char'
    runs = []
    mr = []
    sizes = []
    for r in p:
        if r.tag in (A + 'r', A + 'fld'):
            t = r.findtext(A + 't') or ''
            rp = r.find(A + 'rPr')
            b = rp is not None and rp.get('b') == '1'
            sz = int(rp.get('sz')) / 100 if rp is not None and rp.get('sz') else base_sz
            em = is_emph_color(color_of(rp))
            hl = rp is not None and rp.find(A + 'hlinkClick') is not None
            runs.append({'el': r, 'text': t, 'b': b, 'sz': sz, 'em': em, 'hl': hl})
            if t.strip():
                sizes.append((len(t), sz))
        elif r.tag == A + 'br':
            runs.append({'el': r, 'text': '\n', 'b': False, 'sz': base_sz, 'em': False, 'hl': False})
    txt = ''.join(x['text'] for x in runs)
    return {'runs': runs, 'text': txt, 'lvl': lvl, 'bullet': bullet, 'rtl': bool(HEB.search(txt))}


def shape_base_size(el):
    s = [int(r.get('sz')) / 100 for r in el.iter(A + 'rPr') if r.get('sz')]
    if s:
        s.sort()
        return s[len(s) // 2]
    return 18


def extract_paras(els):
    out = []
    for e in sorted(els, key=lambda e: ((box(e) or [0, 0])[1], -(box(e) or [0])[0])):
        ph = e.find('.//' + P + 'ph')
        phbody = ph is not None and ph.get('type', 'body') in ('body', 'obj') or (ph is not None and ph.get('type') is None)
        base = shape_base_size(e)
        if out:
            out.append(None)
        for p in e.iter(A + 'p'):
            m = para_model(p, base, phbody)
            if m['text'].strip():
                out.append(m)
            else:
                out.append(None)
    # collapse separators
    res = []
    for m in out:
        if m is None and (not res or res[-1] is None):
            continue
        res.append(m)
    while res and res[-1] is None:
        res.pop()
    return res


def mruns(runs, bold_all=False, rel=1.0, base=None):
    out = []
    for r in runs:
        rs = 1.0
        out.append((r['text'], bold_all or r['b'], rs))
    return out


# ---------------- run rendering ----------------
def render_runs(runs, pt, color, bold=None, emph=EMPH, rtl=True):
    xml = []
    for r in runs:
        el = r['el']
        if el.tag == A + 'br':
            xml.append(f'<a:br><a:rPr lang="he-IL" sz="{int(pt * 100)}"/></a:br>')
            continue
        rp = el.find(A + 'rPr')
        attrs = {}
        if rp is not None:
            for k in ('lang', 'i', 'u', 'strike', 'baseline', 'cap'):
                if rp.get(k) is not None:
                    attrs[k] = rp.get(k)
        b = r['b'] if bold is None else bold
        if b:
            attrs['b'] = '1'
        attrs.setdefault('lang', 'he-IL' if HEB.search(r['text']) else 'en-US')
        c = color
        if r['em'] and color in (BODY, NAVY, GRAY):
            c = emph
        if r['hl']:
            c = '1F6FD1' if color in (BODY, NAVY, GRAY) else color
            attrs['u'] = 'sng'
        a = ''.join(f' {k}="{v}"' for k, v in attrs.items())
        inner = solid(c) + '<a:latin typeface="Arial"/><a:cs typeface="Arial"/>'
        if rp is not None:
            h = rp.find(A + 'hlinkClick')
            if h is not None:
                inner += etree.tostring(h).decode()
        t = r['text']
        sp = ' xml:space="preserve"' if t != t.strip() else ''
        xml.append(f'<a:r><a:rPr sz="{int(round(pt * 2)) * 50}"{a} dirty="0">{inner}</a:rPr><a:t{sp}>{esc(t)}</a:t></a:r>')
    return ''.join(xml)


def para_xml(m, pt, color=BODY, bullet=None, bcolor=TEAL, indent=0.0, algn=None, bold=None, before=0.0, after=0.0,
             runs=None, line=None, num=None):
    rtl = m['rtl'] if m else True
    if algn is None:
        algn = 'r' if rtl else 'l'
    rs = m['runs'] if runs is None else runs
    bu = '<a:buNone/>'
    mar = ''
    if bullet:
        ch = {'sq': '■', 'dot': '●', 'dash': '–', 'arrow': '◂' if rtl else '▸', 'chev': '›'}.get(bullet, bullet)
        bsz = 70 if bullet in ('sq', 'dot') else 100
        bu = f'<a:buClr><a:srgbClr val="{bcolor}"/></a:buClr><a:buSzPct val="{bsz * 1000}"/><a:buFont typeface="Arial"/><a:buChar char="{ch}"/>'
        ind = 0.28 * pt / 18
        mar = f' marL="{emu(indent + ind)}" indent="{-emu(ind)}"'
    elif indent:
        mar = f' marL="{emu(indent)}" indent="0"'
    sb = f'<a:spcBef><a:spcPts val="{int(before * 100)}"/></a:spcBef>' if before else '<a:spcBef><a:spcPts val="0"/></a:spcBef>'
    sa = f'<a:spcAft><a:spcPts val="{int(after * 100)}"/></a:spcAft>' if after else ''
    ln = f'<a:lnSpc><a:spcPct val="{int(line * 100000)}"/></a:lnSpc>' if line else '<a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
    return (f'<a:p><a:pPr{mar} algn="{algn}" rtl="{1 if rtl else 0}">{ln}{sb}{sa}{bu}</a:pPr>'
            f'{render_runs(rs, pt, color, bold)}<a:endParaRPr lang="he-IL" sz="{int(pt * 100)}"/></a:p>')


# ---------------- structure analysis ----------------
def split_inline_header(m):
    """'Header: body' with bold header run(s) -> (header_runs, body_runs) or None"""
    runs = m['runs']
    acc = ''
    for i, r in enumerate(runs):
        if not r['b'] and r['text'].strip():
            break
        acc += r['text']
        if acc.rstrip().endswith((':', ':')) and i + 1 < len(runs) and ''.join(x['text'] for x in runs[i + 1:]).strip():
            if 1 < len(acc.strip()) <= 70:
                return runs[:i + 1], runs[i + 1:]
    return None


def is_header(m, nxt, all_ms):
    t = m['text'].strip()
    if len(t) > 75 or nxt is None:
        return False
    bold = all(r['b'] for r in m['runs'] if r['text'].strip())
    big = max([r['sz'] for r in m['runs'] if r['text'].strip()] or [0])
    ws = sorted((r['sz'], len(r['text'])) for x in all_ms for r in x['runs'] if r['text'].strip())
    tot = sum(c for _, c in ws)
    acc = 0
    med = 18
    for sz_, c in ws:
        acc += c
        if acc >= tot / 2:
            med = sz_
            break
    if bold and not all(r['b'] for r in nxt['runs'] if r['text'].strip()):
        return True
    if big >= med * 1.15 and not t.endswith(('.', ',')):
        return True
    if t.endswith((':', ':')) and nxt['lvl'] > m['lvl']:
        return True
    return False


def analyse(ps):
    ms = [m for m in ps if m]
    groups = []  # (header_runs or None, [models])
    i = 0
    for k, m in enumerate(ms):
        nxt = ms[k + 1] if k + 1 < len(ms) else None
        ih = split_inline_header(m)
        if ih and len(m['text']) > 40:
            body = dict(m)
            br = list(ih[1])
            while br and (br[0]['text'] == '\n' or not br[0]['text'].strip()):
                br.pop(0)
            if br and br[0]['text'] != br[0]['text'].lstrip():
                r0 = dict(br[0]); r0['text'] = r0['text'].lstrip(); el = copy.deepcopy(r0['el'])
                tt = el.find(A + 't')
                if tt is not None: tt.text = r0['text']
                r0['el'] = el; br[0] = r0
            body['runs'] = br
            body['text'] = ''.join(r['text'] for r in ih[1])
            groups.append([ih[0], [body], m])
        elif is_header(m, nxt, ms):
            groups.append([m['runs'], [], m])
        else:
            if not groups:
                groups.append([None, [], None])
            groups[-1][1].append(m)
    if all(g[0] is None for g in groups) and ms:
        top = min(m['lvl'] for m in ms)
        tops = [m for m in ms if m['lvl'] == top]
        withsub = 0
        hg = []
        for m in ms:
            if m['lvl'] == top:
                hg.append([m['runs'], [], m])
            elif hg:
                hg[-1][1].append(m)
                if len(hg[-1][1]) == 1:
                    withsub += 1
            else:
                hg = None
                break
        if hg and withsub >= 2 and 2 <= len(tops) <= 6 and all(len(m['text']) <= 120 for m in tops):
            groups = hg
    fixed = []
    for g in groups:
        if g[0] is not None and not g[1] and (not fixed or fixed[-1][0] is None):
            if fixed:
                fixed[-1][1].append(g[2])
            else:
                fixed.append([None, [g[2]], None])
            continue
        fixed.append(g)
    return ms, fixed


# ---------------- title ----------------
def title_parts(t, tel, nel):
    num = ''
    for e in nel:
        num = text(e).strip()
    words = []
    for e in sorted(tel, key=lambda e: ((box(e) or [0, 0])[1])):
        for p in e.iter(A + 'p'):
            segs = ['']
            for ch in p.iter(A + 't', A + 'br'):
                if ch.tag == A + 'br':
                    segs.append('')
                else:
                    segs[-1] += ch.text or ''
            for s in segs:
                s = s.strip()
                if not s or s in ('|', '｜'):
                    continue
                if NUMRE.match(s):
                    num = num or s.strip()
                    continue
                words.append(s)
    words = [re.sub(r'\s*\|\s*$', '', w).strip() for w in words]
    fixed = []
    for w in words:
        m = re.match(r'^(\d+(?:\.\d+)+)\s+(.*)$', w)
        if m and not num:
            num, w = m.group(1), m.group(2)
        fixed.append(w)
    words = [w for w in fixed if w]
    kicker = ''
    if len(words) >= 2 and len(' '.join(words)) > 42:
        kicker, title = words[0], ' '.join(words[1:])
    else:
        title = ' '.join(words)
    return (title, kicker), num


def build_title(ids, tk, num, dark=False):
    title, kicker = tk
    out = []
    right = X1
    if num:
        pw = 0.22 + len(num) * 0.13
        ph = 0.44
        out.append(sp_xml(ids, 'Section Number', right - pw, TITLE_Y + 0.1, pw, ph, 'roundRect', fill=ORANGE,
                          adj={'adj': 50000}, anchor='ctr', ins=(0.02, 0, 0.02, 0),
                          body=simple_para(num, 15, 'FFFFFF', True, 'ctr', False)))
        right = right - pw - 0.15
    width = right - TX0
    pt = 28 if WIDE else 24
    while pt > 16 and wlen(title, pt, 1) * 1.04 > width - 0.1:
        pt -= 0.5
    rtl = bool(HEB.search(title))
    ty = TITLE_Y
    if kicker:
        kp = 13
        out.append(sp_xml(ids, 'Kicker', TX0, TITLE_Y - 0.1, width, 0.3, anchor='ctr', ins=(0.02, 0, 0.02, 0), wrap=False, txbox=True,
                          body=simple_para(kicker, kp, TEAL_D, True, 'r', bool(HEB.search(kicker)))))
        ty = TITLE_Y + 0.14
        pt = min(pt, 24)
    out.append(sp_xml(ids, 'Title', TX0, ty, width, 0.64, anchor='ctr', ins=(0.02, 0, 0.02, 0), wrap=False, ph='title',
                      body=simple_para(title, pt, 'FFFFFF' if dark else NAVY, True, 'r' if rtl else 'r', rtl)))
    # accent under title (from right)
    out.append(sp_xml(ids, 'Title Accent', X1 - 1.15, TITLE_Y + 0.74, 1.15, 0.06, 'rect', fill=TEAL))
    out.append(sp_xml(ids, 'Title Accent 2', X1 - 1.42, TITLE_Y + 0.74, 0.2, 0.06, 'rect', fill=ORANGE))
    return out


# ---------------- illustration ----------------
used_topics = {}
last_ill = [None]


last_tp = [None]


def illus(slide, title, body):
    tp = topic_for(title, body, used_topics, last_tp[0])
    last_tp[0] = tp
    k = used_topics.get(tp, 0)
    used_topics[tp] = k + 1
    v = k % 3
    if last_ill[0] == (tp, v):
        v = (v + 1) % 3
    last_ill[0] = (tp, v)
    path = f'{ILL}/{tp}_{v}.png'
    return add_media(slide, path)


# ---------------- layouts ----------------
def para_mr(m, bold=False):
    return {'mruns': [(r['text'], bold or r['b'], 1.0) for r in m['runs']], 'rel': 1.0}


def text_block(ids, name, x, y, w, h, items, maxpt, minpt, anchor='t', fill=None, line=None, geom='rect', ins=(0.1, 0.06, 0.1, 0.06),
               color=BODY, spacing=0.5, shadow=False, adj=None):
    """items: list of dict(m=model, kind in {'intro','bullet','sub','plain','head','num'}, runs=optional)"""
    iw = w - ins[0] - ins[2]
    ih = h - ins[1] - ins[3]
    meas = []
    for it in items:
        m = it['m']
        runs = it.get('runs', m['runs'])
        rel = {'head': 1.1, 'intro': 1.05, 'sub': 0.9}.get(it['kind'], 1.0)
        ind = {'bullet': 0.3, 'sub': 0.65, 'num': 0.3}.get(it['kind'], 0)
        meas.append({'mruns': [(r['text'], r['b'] or it['kind'] in ('head',), 1.0) for r in runs], 'rel': rel, 'indent': ind,
                     'sp': 0.6 if it['kind'] == 'sub' else 1.0})
    pt = fit_size(meas, iw * 0.97, ih, maxpt, minpt, spacing)
    if pt is None:
        return None, None
    body = []
    for k, it in enumerate(items):
        m = it['m']
        runs = it.get('runs', m['runs'])
        kd = it['kind']
        bef = 0 if k == 0 else pt * spacing * (0.6 if kd == 'sub' else 1.0)
        if kd == 'head':
            body.append(para_xml(m, pt * 1.1, it.get('color', NAVY), None, bold=True, before=bef, runs=runs))
        elif kd == 'intro':
            body.append(para_xml(m, pt * 1.05, it.get('color', NAVY), None, bold=None, before=bef, runs=runs))
        elif kd == 'bullet':
            body.append(para_xml(m, pt, color, it.get('bu', 'sq'), it.get('bc', TEAL), indent=0.02, before=bef, runs=runs))
        elif kd == 'sub':
            body.append(para_xml(m, pt * 0.9, GRAY if color == BODY else color, 'dash', ORANGE, indent=0.35, before=bef, runs=runs))
        else:
            body.append(para_xml(m, pt, it.get('color', color), None, before=bef, runs=runs))
    xml = sp_xml(ids, name, x, y, w, h, geom, fill=fill, line=line, body=''.join(body), anchor=anchor, ins=ins, txbox=True,
                 shadow=shadow, adj=adj)
    return xml, pt


def flat_items(ms, intro=None):
    items = []
    minl = min([m['lvl'] for m in ms] or [0])
    for m in ms:
        if intro is not None and m is intro:
            items.append({'m': m, 'kind': 'intro'})
        elif m['lvl'] > minl:
            items.append({'m': m, 'kind': 'sub'})
        else:
            items.append({'m': m, 'kind': 'bullet' if len(ms) > 1 else 'plain'})
    return items


def detect_intro(ms):
    if len(ms) < 3:
        return None
    f = ms[0]
    t = f['text'].strip()
    if t.endswith((':', ':')):
        return f
    if f['lvl'] < min(m['lvl'] for m in ms[1:]):
        return f
    if f['bullet'] is None and all(m['bullet'] for m in ms[1:]):
        return f
    return None


def L_list_illus(ids, slide, ctx, side='left'):
    ms = ctx['ms']
    intro = detect_intro(ms)
    pw = 3.5 if WIDE else 2.6
    if side == 'left':
        px = X0
        tx, tw = X0 + pw + 0.35, X1 - X0 - pw - 0.35
    else:
        px = X1 - pw
        tx, tw = X0, X1 - X0 - pw - 0.35
    items = flat_items(ms, intro)
    tb, pt = text_block(ids, 'Body', tx, Y0 + 0.1, tw, Y1 - Y0 - 0.1, items, 22, 14, anchor='ctr')
    if not tb:
        return None
    rid = illus(slide, ctx['title'], ctx['body'])
    s = min(pw, Y1 - Y0 - 0.4)
    out = [sp_xml(ids, 'Panel', px, Y0 + 0.1, pw, Y1 - Y0 - 0.1, 'roundRect', fill=SOFT, adj={'adj': 6000}),
           pic_xml(ids, rid, px + (pw - s * 0.9) / 2, Y0 + 0.1 + (Y1 - Y0 - 0.1 - s * 0.9) / 2, s * 0.9, s * 0.9), tb]
    return out


def L_intro_band(ids, slide, ctx):
    ms = ctx['ms']
    intro = detect_intro(ms)
    if intro is None:
        return None
    rest = [m for m in ms if m is not intro]
    # band
    bw = X1 - X0
    band_items = [{'m': intro, 'kind': 'plain', 'color': 'FFFFFF'}]
    iconw = 1.1
    tb, pt = text_block(ids, 'Intro', X0, Y0 + 0.05, bw, 1.25, band_items, 22, 15, anchor='ctr', fill=NAVY, geom='roundRect',
                        ins=(iconw + 0.2, 0.1, 0.3, 0.1), adj={'adj': 12000})
    if not tb:
        tb, pt = text_block(ids, 'Intro', X0, Y0 + 0.05, bw, 1.7, band_items, 20, 13, anchor='ctr', fill=NAVY, geom='roundRect',
                            ins=(iconw + 0.2, 0.1, 0.3, 0.1), adj={'adj': 12000})
        bh = 1.7
        if not tb:
            return None
    else:
        bh = 1.25
    rid = illus(slide, ctx['title'], ctx['body'])
    out = [tb, pic_xml(ids, rid, X0 + 0.12, Y0 + 0.05 + (bh - 1.0) / 2, 1.0, 1.0)]
    items = flat_items(rest)
    top = Y0 + bh + 0.3
    avail = Y1 - top
    n = len(items)
    tops = [it for it in items if it['kind'] != 'sub']
    if n >= 6 and len(tops) == n and sum(len(i['m']['text']) for i in items) / n < 120:
        half = (n + 1) // 2
        cw = (bw - 0.4) / 2
        a, pa = text_block(ids, 'Column 1', X1 - cw, top, cw, avail, items[:half], 20, 13)
        b, pb = text_block(ids, 'Column 2', X0, top, cw, avail, items[half:], 20, 13)
        if a and b:
            # harmonise sizes
            p = min(pa, pb)
            a, _ = text_block(ids, 'Column 1', X1 - cw, top, cw, avail, items[:half], p, p)
            b, _ = text_block(ids, 'Column 2', X0, top, cw, avail, items[half:], p, p)
            out += [a, b, line_xml(ids, X0 + cw + 0.2, top + 0.1, X0 + cw + 0.2, top + avail - 0.2, LINE, 1.25)]
            return out
    tb2, _ = text_block(ids, 'Body', X0, top, bw, avail, items, 20, 13)
    if not tb2:
        return None
    return out + [tb2]


def L_numbered(ids, slide, ctx):
    ms = ctx['ms']
    intro = detect_intro(ms)
    rest = [m for m in ms if m is not intro]
    if not (2 <= len(rest) <= 7) or any(m['lvl'] > rest[0]['lvl'] for m in rest):
        return None
    out = []
    top = Y0 + 0.05
    if intro:
        tb, pt = text_block(ids, 'Intro', X0, top, X1 - X0, 0.9, [{'m': intro, 'kind': 'intro'}], 22, 15, anchor='ctr')
        if not tb:
            return None
        out.append(tb)
        top += 1.0
    n = len(rest)
    numd = all(m['bullet'] == 'num' for m in rest)
    gap = 0.14
    rh = (Y1 - top - gap * (n - 1)) / n
    if rh < 0.5:
        return None
    circ = min(0.62, rh - 0.12)
    # common font size
    tw = X1 - X0 - circ - 0.45
    pts = []
    for m in rest:
        it = [{'m': m, 'kind': 'plain'}]
        meas = [{'mruns': [(r['text'], r['b'], 1.0) for r in m['runs']], 'rel': 1}]
        p = fit_size(meas, (tw - 0.3) * 0.97, rh - 0.12, 21, 13)
        if p is None:
            return None
        pts.append(p)
    pt = min(pts)
    for k, m in enumerate(rest):
        y = top + k * (rh + gap)
        fill = SOFT if k % 2 == 0 else 'FFFFFF'
        out.append(sp_xml(ids, f'Row {k + 1}', X0, y, X1 - X0, rh, 'roundRect', fill=fill, line=LINE, lw=0.75, adj={'adj': 10000}))
        out.append(sp_xml(ids, f'Number {k + 1}', X1 - circ - 0.15, y + (rh - circ) / 2, circ, circ, 'ellipse',
                          fill=ORANGE if k % 2 else NAVY, anchor='ctr', ins=(0, 0, 0, 0),
                          body=simple_para(str(k + 1) if numd else '✓', min(20, circ * 30), 'FFFFFF', True, 'ctr', False)))
        tb, _ = text_block(ids, f'Item {k + 1}', X0 + 0.15, y, tw, rh, [{'m': m, 'kind': 'plain'}], pt, pt, anchor='ctr')
        out.append(tb)
    return out


def card_grid(ids, n, top, bottom, cols):
    rows = (n + cols - 1) // cols
    gx, gy = 0.25, 0.25
    cw = (X1 - X0 - gx * (cols - 1)) / cols
    ch = (bottom - top - gy * (rows - 1)) / rows
    pos = []
    for k in range(n):
        r, c = divmod(k, cols)
        # RTL: first column on the right
        x = X1 - (c + 1) * cw - c * gx
        cnt = cols if r < rows - 1 else n - cols * (rows - 1)
        if r == rows - 1 and cnt < cols:  # centre last row
            off = (cols - cnt) * (cw + gx) / 2
            x -= off
        pos.append((x, top + r * (ch + gy), cw, ch))
    return pos


def L_cards(ids, slide, ctx, style=0):
    groups = ctx['groups']
    intro_ms = []
    gs = []
    for h, body, m in groups:
        if h is None:
            if gs:
                return None
            intro_ms += body
        else:
            gs.append((h, body, m))
    n = len(gs)
    if not (2 <= n <= 6):
        return None
    out = []
    top = Y0 + 0.05
    if intro_ms:
        items = flat_items(intro_ms)
        tb, pt = text_block(ids, 'Intro', X0, top, X1 - X0, 1.0, items, 21, 14, anchor='ctr')
        if not tb:
            return None
        out.append(tb)
        top += 1.1
    cols = 2 if n in (2, 4) else 3
    if n == 2 and WIDE:
        cols = 2
    pos = card_grid(ids, n, top, Y1, cols)
    # common size
    best = None
    for pt in [x / 2 for x in range(40, 23, -1)]:
        ok = True
        for (h, body, m), (x, y, w, hh) in zip(gs, pos):
            hm = [{'mruns': [(r['text'], True, 1.0) for r in h], 'rel': 1.1}]
            bm = [{'mruns': [(r['text'], r['b'], 1.0) for r in b['runs']], 'rel': 1.0, 'indent': 0.3 if len(body) > 1 else 0} for b in body]
            need = block_height(hm, w - 0.5, pt) + 0.25 + (block_height(bm, w - 0.4, pt) if bm else 0)
            if need > hh - 0.35:
                ok = False
                break
        if ok:
            best = pt
            break
    if best is None:
        return None
    pt = best
    accents = [TEAL, ORANGE, NAVY]
    for k, ((h, body, m), (x, y, w, hh)) in enumerate(zip(gs, pos)):
        acc = accents[k % 3]
        if style == 0:
            out.append(sp_xml(ids, f'Card {k + 1}', x, y, w, hh, 'roundRect', fill='FFFFFF', line=LINE, lw=1, adj={'adj': 7000}, shadow=True))
            out.append(sp_xml(ids, f'Card Accent {k + 1}', x + w - 0.09, y + 0.18, 0.09, hh - 0.36, 'rect', fill=acc))
            hc = NAVY
        else:
            out.append(sp_xml(ids, f'Card {k + 1}', x, y, w, hh, 'roundRect', fill=SOFT, adj={'adj': 7000}))
            out.append(sp_xml(ids, f'Card Head {k + 1}', x, y, w, 0.12, 'rect', fill=acc))
            hc = NAVY
        hm = [{'mruns': [(r['text'], True, 1.0) for r in h], 'rel': 1.1}]
        hh_ = block_height(hm, w - 0.5, pt) + 0.15
        hx = sp_xml(ids, f'Card Title {k + 1}', x + 0.15, y + 0.2, w - 0.35, hh_, anchor='t', ins=(0.05, 0.02, 0.05, 0.02), txbox=True,
                    body=para_xml(m, pt * 1.1, hc, None, bold=True, runs=h))
        out.append(hx)
        if body:
            items = [{'m': b, 'kind': 'bullet' if len(body) > 1 else 'plain'} for b in body]
            tb, _ = text_block(ids, f'Card Text {k + 1}', x + 0.15, y + 0.25 + hh_, w - 0.35, hh - hh_ - 0.4, items, pt, pt)
            if tb is None:
                return None
            out.append(tb)
    return out


def L_accordion(ids, slide, ctx):
    groups = ctx['groups']
    gs = [(h, b, m) for h, b, m in groups if h is not None]
    pre = [b for h, bb, m in groups if h is None for b in bb]
    if len(gs) < 2 or len(gs) > 9:
        return None
    out = []
    top = Y0 + 0.02
    if pre:
        tb, pt = text_block(ids, 'Intro', X0, top, X1 - X0, 0.95, flat_items(pre), 20, 13, anchor='ctr')
        if not tb:
            return None
        out.append(tb)
        top += 1.0
    n = len(gs)
    hw = 2.7 if WIDE else 2.2
    bw = X1 - X0 - hw - 0.2
    # allocate heights proportional to needed lines at a common size
    for pt in [x / 2 for x in range(38, 21, -1)]:
        need = []
        for h, body, m in gs:
            bm = [{'mruns': [(r['text'], r['b'], 1.0) for r in b['runs']], 'rel': 1.0} for b in body]
            hm = [{'mruns': [(r['text'], True, 1.0) for r in h], 'rel': 1.0}]
            need.append(max(block_height(bm, bw - 0.3, pt, 0.3) if bm else 0, block_height(hm, hw - 0.3, pt)) + 0.2)
        if sum(need) + 0.1 * (n - 1) <= Y1 - top:
            break
    else:
        return None
    extra = (Y1 - top - sum(need) - 0.1 * (n - 1)) / n
    extra = min(extra, 0.35)
    y = top
    for k, ((h, body, m), nd) in enumerate(zip(gs, need)):
        hh = nd + extra
        out.append(sp_xml(ids, f'Head {k + 1}', X1 - hw, y, hw, hh, 'roundRect', fill=NAVY if k % 2 == 0 else TEAL_D, adj={'adj': 14000},
                          anchor='ctr', ins=(0.12, 0.04, 0.15, 0.04), body=para_xml(m, pt, 'FFFFFF', None, bold=True, runs=h)))
        if body:
            items = [{'m': b, 'kind': 'plain'} for b in body]
            tb, _ = text_block(ids, f'Body {k + 1}', X0, y, bw, hh, items, pt, pt, anchor='ctr', fill=SOFT if k % 2 == 0 else 'FFFFFF',
                               line=LINE, geom='roundRect', ins=(0.15, 0.04, 0.15, 0.04), spacing=0.3, adj={'adj': 8000})
            if tb is None:
                tb, _ = text_block(ids, f'Body {k + 1}', X0, y, bw, hh, items, pt, pt - 2, anchor='ctr', fill=SOFT, line=LINE,
                                   geom='roundRect', ins=(0.15, 0.04, 0.15, 0.04), spacing=0.2, adj={'adj': 8000})
                if tb is None:
                    return None
            out.append(tb)
        y += hh + 0.1
    return out


def L_statement(ids, slide, ctx):
    ms = ctx['ms']
    tot = sum(len(m['text']) for m in ms)
    if len(ms) > 3 or tot > 420:
        return None
    pw = 3.3 if WIDE else 2.4
    bx = X0 + pw + 0.3
    bw = X1 - bx
    items = [{'m': m, 'kind': 'plain', 'color': NAVY if k == 0 else BODY} for k, m in enumerate(ms)]
    tb, pt = text_block(ids, 'Statement', bx, Y0 + 0.4, bw, Y1 - Y0 - 0.8, items, 30, 18, anchor='ctr', fill=TINT, geom='roundRect',
                        ins=(0.45, 0.3, 0.6, 0.3), adj={'adj': 8000})
    if not tb:
        return None
    rid = illus(slide, ctx['title'], ctx['body'])
    s = pw
    out = [tb, sp_xml(ids, 'Statement Bar', X1 - 0.16, Y0 + 0.75, 0.16, Y1 - Y0 - 1.5, 'rect', fill=TEAL),
           pic_xml(ids, rid, X0, Y0 + (Y1 - Y0 - s) / 2, s, s)]
    return out


def L_split_dark(ids, slide, ctx):
    ms = ctx['ms']
    intro = detect_intro(ms)
    if intro is None:
        return None
    rest = [m for m in ms if m is not intro]
    pw = 4.1 if WIDE else 3.2
    tb, pt = text_block(ids, 'Lead', X1 - pw, Y0 + 0.05, pw, Y1 - Y0 - 0.05, [{'m': intro, 'kind': 'plain', 'color': 'FFFFFF'}], 24, 15,
                        anchor='b', fill=NAVY, geom='roundRect', ins=(0.3, 1.9 if WIDE else 1.5, 0.3, 0.35), adj={'adj': 6000})
    if not tb:
        return None
    rid = illus(slide, ctx['title'], ctx['body'])
    s = 1.55 if WIDE else 1.2
    out = [tb, sp_xml(ids, 'Lead Disc', X1 - pw / 2 - s / 2 - 0.08, Y0 + 0.2, s + 0.16, s + 0.16, 'ellipse', fill='FFFFFF'),
           pic_xml(ids, rid, X1 - pw / 2 - s / 2, Y0 + 0.28, s, s)]
    tb2, _ = text_block(ids, 'Body', X0, Y0 + 0.05, X1 - X0 - pw - 0.35, Y1 - Y0 - 0.05, flat_items(rest), 21, 13, anchor='ctr')
    if not tb2:
        return None
    return out + [tb2]


def L_steps(ids, slide, ctx):
    ms = ctx['ms']
    intro = detect_intro(ms)
    rest = [m for m in ms if m is not intro]
    n = len(rest)
    if not (3 <= n <= 5) or any(len(m['text']) > 110 for m in rest) or any(m['lvl'] != rest[0]['lvl'] for m in rest):
        return None
    out = []
    top = Y0 + 0.1
    if intro:
        tb, pt = text_block(ids, 'Intro', X0, top, X1 - X0, 1.0, [{'m': intro, 'kind': 'intro'}], 22, 15, anchor='ctr')
        if not tb:
            return None
        out.append(tb)
        top += 1.2
    gap = 0.18
    cw = (X1 - X0 - gap * (n - 1)) / n
    ch = min(3.6, Y1 - top - 0.2)
    y = top + (Y1 - top - ch) / 2
    pts = []
    for m in rest:
        meas = [{'mruns': [(r['text'], r['b'], 1.0) for r in m['runs']], 'rel': 1}]
        p = fit_size(meas, (cw - 0.4) * 0.97, ch - 1.35, 20, 13)
        if p is None:
            return None
        pts.append(p)
    pt = min(pts)
    for k, m in enumerate(rest):
        x = X1 - (k + 1) * cw - k * gap
        out.append(sp_xml(ids, f'Step {k + 1}', x, y, cw, ch, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 8000}, shadow=True))
        out.append(sp_xml(ids, f'Step Band {k + 1}', x, y, cw, 0.95, 'round2SameRect', fill=NAVY if k % 2 == 0 else TEAL_D, adj={'adj1': 16000, 'adj2': 0},
                          anchor='ctr', body=simple_para(f'{k + 1:02d}', 26, 'FFFFFF', True, 'ctr', False)))
        if k < n - 1:
            out.append(sp_xml(ids, f'Step Arrow {k + 1}', x - gap / 2 - 0.17, y + 0.3, 0.34, 0.36, 'triangle', fill=ORANGE, rot=270))
        tb, _ = text_block(ids, f'Step Text {k + 1}', x + 0.1, y + 1.1, cw - 0.2, ch - 1.25, [{'m': m, 'kind': 'plain'}], pt, pt, anchor='t')
        out.append(tb)
    return out


def L_plain(ids, slide, ctx, minpt=11):
    ms = ctx['ms']
    intro = detect_intro(ms)
    groups = ctx['groups']
    items = []
    if any(h for h, b, m in groups):
        for h, body, m in groups:
            if h is not None:
                hm = dict(m)
                items.append({'m': m, 'kind': 'head', 'runs': h, 'color': TEAL_D})
            items += [{'m': b, 'kind': 'plain'} for b in body]
    else:
        items = flat_items(ms, intro)
    out = [sp_xml(ids, 'Side Accent', X1 - 0.08, Y0 + 0.1, 0.08, Y1 - Y0 - 0.2, 'rect', fill=TEAL)]
    tb, pt = text_block(ids, 'Body', X0, Y0, X1 - X0 - 0.3, Y1 - Y0, items, 20, minpt, spacing=0.4)
    if not tb:
        tb, pt = text_block(ids, 'Body', X0, Y0, X1 - X0 - 0.3, Y1 - Y0 + 0.1, items, 12, 8, spacing=0.2)
    return out + [tb]


def L_figure(ids, slide, ctx, figs):
    """text on the right, figure(s) on the left"""
    ms = ctx['ms']
    fw = (X1 - X0) * 0.48
    out = []
    if ms:
        intro = detect_intro(ms)
        tb, pt = text_block(ids, 'Body', X0 + fw + 0.35, Y0 + 0.1, X1 - X0 - fw - 0.35, Y1 - Y0 - 0.1, flat_items(ms, intro), 21, 12, anchor='ctr')
        if not tb:
            tb, pt = text_block(ids, 'Body', X0 + fw + 0.35, Y0, X1 - X0 - fw - 0.35, Y1 - Y0, flat_items(ms, intro), 12, 9)
        out.append(tb)
    else:
        fw = X1 - X0
    out.append(sp_xml(ids, 'Figure Card', X0, Y0 + 0.1, fw, Y1 - Y0 - 0.1, 'roundRect', fill='FFFFFF', line=LINE, adj={'adj': 4000}, shadow=True))
    fy = Y0 + 0.3
    fh = (Y1 - Y0 - 0.5 - 0.2 * (len(figs) - 1)) / len(figs)
    for k, f in enumerate(figs):
        out += f(ids, X0 + 0.2, fy + k * (fh + 0.2), fw - 0.4, fh)
    return out


def items_meas(items):
    meas = []
    for it in items:
        m = it['m']
        runs = it.get('runs', m['runs'])
        rel = {'head': 1.1, 'intro': 1.05, 'sub': 0.9}.get(it['kind'], 1.0)
        ind = {'bullet': 0.3, 'sub': 0.65, 'num': 0.3}.get(it['kind'], 0)
        meas.append({'mruns': [(r['text'], r['b'] or it['kind'] in ('head',), 1.0) for r in runs], 'rel': rel, 'indent': ind,
                     'sp': 0.6 if it['kind'] == 'sub' else 1.0})
    return meas


def fit_items(items, w, h, maxpt, minpt, ins=(0.1, 0.06, 0.1, 0.06), spacing=0.5):
    return fit_size(items_meas(items), (w - ins[0] - ins[2]) * 0.97, h - ins[1] - ins[3], maxpt, minpt, spacing)


def group_items(h, body, m, hc=TEAL_D):
    its = []
    if h is not None:
        its.append({'m': m, 'kind': 'head', 'runs': h, 'color': hc})
    its += [{'m': b, 'kind': 'plain' if len(body) == 1 else 'bullet'} for b in body]
    return its


def L_cols(ids, slide, ctx):
    groups = ctx['groups']
    if len(groups) < 3:
        return None
    its = [group_items(h, b, m) for h, b, m in groups]
    sizes = [len(' '.join(x['m']['text'] for x in g)) for g in its]
    tot = sum(sizes)
    # split point balancing text
    best, acc = 1, 0
    for k in range(1, len(its)):
        acc += sizes[k - 1]
        if acc >= tot / 2:
            best = k if abs(acc - tot / 2) < abs(acc - sizes[k - 1] - tot / 2) else max(1, k - 1)
            break
    c1 = [x for g in its[:best] for x in g]
    c2 = [x for g in its[best:] for x in g]
    cw = (X1 - X0 - 0.6) / 2
    p1 = fit_items(c1, cw, Y1 - Y0 - 0.05, 21, 12)
    p2 = fit_items(c2, cw, Y1 - Y0 - 0.05, 21, 12)
    if not p1 or not p2:
        return None
    p = min(p1, p2)
    a, _ = text_block(ids, 'Column 1', X1 - cw, Y0 + 0.05, cw, Y1 - Y0 - 0.05, c1, p, p)
    b, _ = text_block(ids, 'Column 2', X0, Y0 + 0.05, cw, Y1 - Y0 - 0.05, c2, p, p)
    return [sp_xml(ids, 'Column Rule', X0 + cw + 0.27, Y0 + 0.2, 0.06, Y1 - Y0 - 0.4, 'rect', fill=TINT), a, b]


def L_timeline(ids, slide, ctx):
    groups = ctx['groups']
    gs = [g for g in groups]
    n = len(gs)
    if not (2 <= n <= 7):
        return None
    lx = X1 - 0.3
    tw = lx - 0.35 - X0
    for pt in [x / 2 for x in range(40, 23, -1)]:
        need = [block_height(items_meas(group_items(h, b, m)), (tw - 0.2) * 0.97, pt, 0.3) + 0.12 for h, b, m in gs]
        if sum(need) + 0.18 * (n - 1) <= Y1 - Y0 - 0.1:
            break
    else:
        return None
    out = [sp_xml(ids, 'Timeline', lx - 0.025, Y0 + 0.2, 0.05, Y1 - Y0 - 0.4, 'rect', fill=TINT)]
    gap = min(0.45, (Y1 - Y0 - 0.1 - sum(need)) / max(1, n - 1)) if n > 1 else 0
    y = Y0 + 0.05 + max(0, (Y1 - Y0 - 0.1 - sum(need) - gap * (n - 1)) / 2)
    for k, ((h, b, m), nd) in enumerate(zip(gs, need)):
        out.append(sp_xml(ids, f'Timeline Dot {k + 1}', lx - 0.14, y + 0.06, 0.28, 0.28, 'ellipse', fill='FFFFFF', line=[TEAL, ORANGE, NAVY][k % 3], lw=3))
        tb, _ = text_block(ids, f'Timeline Item {k + 1}', X0, y, tw, nd + 0.05, group_items(h, b, m, NAVY), pt, pt - 1, spacing=0.3)
        if tb is None:
            return None
        out.append(tb)
        y += nd + gap
    return out


def L_illus_corner(ids, slide, ctx):
    ms = ctx['ms']
    intro = detect_intro(ms)
    items = flat_items(ms, intro)
    s = 2.7 if WIDE else 2.1
    tw = X1 - X0 - s - 0.2
    tb, pt = text_block(ids, 'Body', X0 + s + 0.2, Y0 + 0.1, tw, Y1 - Y0 - 0.1, items, 22, 14, anchor='ctr', fill='FFFFFF', line=LINE,
                        geom='roundRect', ins=(0.35, 0.25, 0.45, 0.25), adj={'adj': 5000}, shadow=True)
    if not tb:
        return None
    rid = illus(slide, ctx['title'], ctx['body'])
    return [sp_xml(ids, 'Halo', X0 - 0.2, Y1 - s - 0.9, s + 0.9, s + 0.9, 'ellipse', fill=TINT),
            pic_xml(ids, rid, X0, Y1 - s - 0.5, s, s), tb,
            sp_xml(ids, 'Card Edge', X1 - 0.1, Y0 + 0.5, 0.1, Y1 - Y0 - 0.9, 'rect', fill=ORANGE)]


SIMPLE_ORDER = ['cards', 'accordion', 'steps', 'numbered', 'band', 'split', 'illus_l', 'statement', 'illus_r']


def choose(ids, slide, ctx, last):
    groups = ctx['groups']
    hdr = [g for g in groups if g[0] is not None]
    nohdr_pre = all(g[0] is not None for g in groups[1:])
    cands = []
    if len(hdr) >= 2 and nohdr_pre:
        cands = ['cards0', 'timeline', 'cols', 'accordion', 'cards1']
    else:
        ms = ctx['ms']
        tot = sum(len(m['text']) for m in ms)
        if len(ms) <= 3 and tot <= 420:
            cands = ['statement', 'illus_l', 'illus_c', 'illus_r']
        else:
            intro = detect_intro(ms)
            short = all(len(m['text']) <= 110 for m in ms)
            cands = []
            if intro:
                cands += ['band', 'split']
            if short and 3 <= len(ms) - (1 if intro else 0) <= 5:
                cands += ['steps']
            if 2 <= len(ms) - (1 if intro else 0) <= 7:
                cands += ['numbered']
            cands += ['illus_l', 'illus_c', 'illus_r']
    # rotate so the same layout doesn't repeat
    pitems = []
    for h, b, m in groups:
        pitems += group_items(h, b, m) if h is not None else flat_items(b)
    pfull = fit_items(pitems, X1 - X0 - 0.3, Y1 - Y0, 20, 8, spacing=0.4) or 8
    if pfull < 14.5:
        cands = ['cols', 'plain'] if len(groups) >= 3 else ['plain']
    cnt = ctx['counter']
    k = cnt.get(tuple(cands), 0)
    cnt[tuple(cands)] = k + 1
    rot = cands[k % len(cands):] + cands[:k % len(cands)]
    rot = [c for c in rot if c != last] + [c for c in rot if c == last]
    fns = {'cards0': lambda: L_cards(ids, slide, ctx, 0), 'cards1': lambda: L_cards(ids, slide, ctx, 1),
           'accordion': lambda: L_accordion(ids, slide, ctx), 'cols': lambda: L_cols(ids, slide, ctx),
           'timeline': lambda: L_timeline(ids, slide, ctx), 'illus_c': lambda: L_illus_corner(ids, slide, ctx), 'plain': lambda: L_plain(ids, slide, ctx), 'steps': lambda: L_steps(ids, slide, ctx),
           'numbered': lambda: L_numbered(ids, slide, ctx), 'band': lambda: L_intro_band(ids, slide, ctx),
           'split': lambda: L_split_dark(ids, slide, ctx), 'illus_l': lambda: L_list_illus(ids, slide, ctx, 'left'),
           'illus_r': lambda: L_list_illus(ids, slide, ctx, 'right'), 'statement': lambda: L_statement(ids, slide, ctx)}
    for c in rot + (['accordion', 'illus_l', 'band', 'numbered'] if 'plain' not in cands else []):
        if c not in fns:
            continue
        r = fns[c]()
        if r and all(x is not None for x in r):
            return c, r
    return 'plain', L_plain(ids, slide, ctx)


# ---------------- agenda ----------------
def L_agenda(ids, slide, ctx, items, cur):
    """items: list of (num, text); cur: index highlighted or None; ctx['head'] optional heading"""
    out = []
    pw = 4.3 if WIDE else 3.3
    out.append(sp_xml(ids, 'Agenda Panel', X1 - pw, Y0 + 0.05, pw, Y1 - Y0 - 0.05, 'roundRect', fill=NAVY, adj={'adj': 5000}))
    big = items[cur][0] if cur is not None else ctx.get('bignum', '')
    head = items[cur][1] if cur is not None else ctx.get('head', '')
    sub = ctx.get('kicker', 'הנושא הבא' if cur is not None else '')
    body = ''
    if sub:
        body += simple_para(sub, 14, TEAL, True, 'r', True)
    if big:
        body += simple_para(big, 54 if WIDE else 44, TEAL, True, 'r', False)
    if head:
        hp = 26
        while hp > 16 and para_lines([(head, True, 1)], pw - 0.7, hp) > 3:
            hp -= 1
        body += simple_para(head, hp, 'FFFFFF', True, 'r', True)
    out.append(sp_xml(ids, 'Agenda Current', X1 - pw + 0.1, Y0 + 0.4, pw - 0.3, Y1 - Y0 - 0.9, anchor='b', ins=(0.15, 0.1, 0.25, 0.3), body=body, txbox=True))
    rid = illus(slide, head or ctx['title'], '')
    out.append(pic_xml(ids, rid, X1 - pw + 0.3, Y0 + 0.3, 1.5, 1.5))
    lx0, lx1 = X0, X1 - pw - 0.35
    n = len(items)
    rh = min(0.62, (Y1 - Y0 - 0.1) / n)
    top = Y0 + 0.05 + (Y1 - Y0 - 0.05 - rh * n) / 2
    pt = 18
    while pt > 11 and any(wlen(t, pt, 1) > lx1 - lx0 - 1.3 for _, t in items):
        pt -= 0.5
    pt = min(pt, rh * 30)
    for k, (num, t) in enumerate(items):
        y = top + k * rh
        on = k == cur
        if on:
            out.append(sp_xml(ids, f'Agenda Row {k + 1}', lx0, y + 0.05, lx1 - lx0, rh - 0.1, 'roundRect', fill=ORANGE, adj={'adj': 50000}))
        else:
            out.append(line_xml(ids, lx0 + 0.1, y + rh, lx1 - 0.1, y + rh, LINE, 0.75))
        if num:
            out.append(sp_xml(ids, f'Agenda Num {k + 1}', lx1 - 1.0, y, 0.9, rh, anchor='ctr', ins=(0, 0, 0.1, 0), txbox=True,
                              body=simple_para(num, pt, 'FFFFFF' if on else TEAL_D, True, 'r', False)))
        out.append(sp_xml(ids, f'Agenda Item {k + 1}', lx0 + 0.15, y, lx1 - lx0 - 1.2, rh, anchor='ctr', ins=(0.05, 0, 0.05, 0), txbox=True, wrap=False,
                          body=simple_para(t, pt, 'FFFFFF' if on else (NAVY if cur is None else GRAY), on or cur is None, 'r', True)))
    return out


def L_tiles(ids, slide, ctx, tiles, intro):
    n = len(tiles)
    out = []
    top = Y0 + 0.05
    if intro:
        tb, pt = text_block(ids, 'Intro', X0, top, X1 - X0, 0.9, flat_items(intro), 21, 14, anchor='ctr')
        if tb:
            out.append(tb)
            top += 1.0
    cols = 3 if n in (3, 5, 6, 9) else (4 if n in (7, 8) and WIDE else 2 if n <= 4 else 3)
    pos = card_grid(ids, n, top, Y1, cols)
    pts = [fit_items([{'m': m, 'kind': 'plain'} for m in t], w - 0.24, hh - 0.6, 20, 11, spacing=0.3) for t, (x, y, w, hh) in zip(tiles, pos)]
    if not all(pts):
        return None
    best = min(pts)
    for k, (t, (x, y, w, hh)) in enumerate(zip(tiles, pos)):
        acc = [TEAL, ORANGE, NAVY][k % 3]
        out.append(sp_xml(ids, f'Tile {k + 1}', x, y, w, hh, 'roundRect', fill=SOFT, adj={'adj': 9000}))
        out.append(sp_xml(ids, f'Tile Accent {k + 1}', x + w - 0.75, y + 0.22, 0.5, 0.09, 'roundRect', fill=acc, adj={'adj': 50000}))
        tb, _ = text_block(ids, f'Tile Text {k + 1}', x + 0.12, y + 0.4, w - 0.24, hh - 0.6, [{'m': m, 'kind': 'plain'} for m in t], best, best,
                           anchor='ctr', spacing=0.3)
        out.append(tb)
    return out


# ---------------- complex restyle ----------------
import colorsys


def map_color(c, role='fill'):
    r, g, b = int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l > 0.95:
        return c
    if role == 'text':
        if s < 0.25 or l < 0.3:
            return BODY if l < 0.6 else c
        if l > 0.85:
            return c
        if h < 0.17 or h > 0.92:
            return OR_D
        return EMPH if h < 0.55 else NAVY
    if s < 0.18:
        if l > 0.8:
            return 'F1F4F8'
        if l > 0.45:
            return 'A9B1C2'
        return NAVY if l < 0.25 else '4A4968'
    if l < 0.22:
        return NAVY
    if h < 0.17 or h > 0.92:
        return 'FDE7CC' if l > 0.8 else ORANGE
    if l > 0.8:
        return TINT
    if h > 0.55:
        return NAVY if l < 0.45 else '3D5A9E' if False else TEAL_D
    return TEAL if l > 0.5 else TEAL_D


def lum(c):
    r, g, b = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def recolor_tree(el):
    for clr in el.iter(A + 'srgbClr'):
        par = clr.getparent()
        role = 'fill'
        anc = par.getparent()
        if anc is not None and anc.tag in (A + 'rPr', A + 'defRPr', A + 'endParaRPr'):
            role = 'text'
        if par.tag in (A + 'solidFill', A + 'gs') or par.tag == A + 'buClr':
            v = clr.get('val')
            if v and len(v) == 6:
                clr.set('val', map_color(v.upper(), role))


def fix_contrast(sp):
    sppr = sp.find(P + 'spPr')
    if sppr is None:
        return
    f = sppr.find(A + 'solidFill')
    if f is None or f.find(A + 'srgbClr') is None:
        return
    fc = f.find(A + 'srgbClr').get('val')
    dark = lum(fc) < 0.45
    for r in sp.iter(A + 'rPr', A + 'endParaRPr'):
        sf = r.find(A + 'solidFill')
        if sf is not None and sf.find(A + 'srgbClr') is not None:
            tc = sf.find(A + 'srgbClr').get('val')
            if dark and lum(tc) < 0.5:
                sf.find(A + 'srgbClr').set('val', 'FFFFFF')
            elif not dark and lum(tc) > 0.75:
                sf.find(A + 'srgbClr').set('val', NAVY)
        elif sf is None and dark and r.tag == A + 'rPr':
            r.insert(0, frag(f'<a:solidFill xmlns:a="{NSA}"><a:srgbClr val="FFFFFF"/></a:solidFill>'))


def round_boxes(el):
    for sp in el.iter(P + 'sp'):
        sppr = sp.find(P + 'spPr')
        if sppr is None:
            continue
        g = sppr.find(A + 'prstGeom')
        b = box(sp)
        if g is None or g.get('prst') != 'rect' or not b or b[2] < 0.5 or b[3] < 0.35:
            continue
        filled = sppr.find(A + 'solidFill') is not None
        ln = sppr.find(A + 'ln')
        lined = ln is not None and ln.find(A + 'noFill') is None and len(ln)
        if (filled or lined) and text(sp):
            g.set('prst', 'roundRect')
            av = g.find(A + 'avLst')
            av.clear() if av is not None else None
            if av is None:
                av = etree.SubElement(g, A + 'avLst')
            gd = etree.SubElement(av, A + 'gd')
            gd.set('name', 'adj')
            gd.set('fmla', 'val %d' % min(16000, int(0.09 / min(b[2], b[3]) * 50000)))


def restyle_table(gf):
    tbl = gf.find('.//' + A + 'tbl')
    if tbl is None:
        return
    tp = tbl.find(A + 'tblPr')
    for k, tr in enumerate(tbl.findall(A + 'tr')):
        for tc in tr.findall(A + 'tc'):
            tcpr = tc.find(A + 'tcPr')
            if tcpr is None:
                tcpr = etree.SubElement(tc, A + 'tcPr')
            for ch in list(tcpr):
                if ch.tag in (A + 'solidFill', A + 'noFill', A + 'gradFill', A + 'lnL', A + 'lnR', A + 'lnT', A + 'lnB'):
                    tcpr.remove(ch)
            fill = NAVY if k == 0 else (SOFT if k % 2 == 0 else 'FFFFFF')
            for i, side in enumerate(('lnL', 'lnR', 'lnT', 'lnB')):
                ln = frag(f'<a:{side} xmlns:a="{NSA}" w="9525">{solid(LINE)}</a:{side}>')
                tcpr.insert(i, ln)
            tcpr.append(frag(f'<a:solidFill xmlns:a="{NSA}"><a:srgbClr val="{fill}"/></a:solidFill>'))
            for r in tc.iter(A + 'rPr', A + 'endParaRPr'):
                for sf in r.findall(A + 'solidFill'):
                    r.remove(sf)
                r.insert(0, frag(f'<a:solidFill xmlns:a="{NSA}"><a:srgbClr val="{"FFFFFF" if k == 0 else BODY}"/></a:solidFill>'))
                if k == 0:
                    r.set('b', '1')


done_parts = set()


def recolor_part(name):
    if name in done_parts or name not in parts:
        return
    done_parts.add(name)
    t = etree.fromstring(parts[name])
    recolor_tree(t)
    parts[name] = etree.tostring(t, xml_declaration=True, encoding='UTF-8', standalone=True)


def slide_rel_map(slide):
    rel = parts[rels_name(slide)].decode()
    return {re.search(r'Id="([^"]+)"', r).group(1): re.search(r'Target="([^"]+)"', r).group(1) for r in re.findall(r'<Relationship [^>]*>', rel)}


def fit_box(x, y, w, h, iw, ih):
    s = min(w / iw, h / ih)
    return x + (w - iw * s) / 2, y + (h - ih * s) / 2, iw * s, ih * s


def img_size(slide, rid):
    rm = slide_rel_map(slide)
    p = os.path.normpath(os.path.join('ppt/slides', rm[rid])).replace('\\', '/')
    try:
        im = Image.open(io.BytesIO(parts[p]))
        return im.size
    except Exception:
        return (4, 3)


def frame_fig(slide, rid, descr=''):
    iw, ih = img_size(slide, rid)

    def f(ids, x, y, w, h):
        a, b, c, d = fit_box(x, y, w, h, iw, ih)
        return [pic_xml(ids, rid, a, b, c, d, 'Figure', descr)]
    return f


# ---------------- main ----------------
def max_id(t):
    return max([int(x.get('id')) for x in t.iter(P + 'cNvPr') if x.get('id', '').isdigit()] or [1])


def label_pics(tr):
    out = {}
    k = 0
    for el in tr.iter(P + 'pic'):
        nm = el.find('.//' + P + 'cNvPr').get('name') or ''
        if nm.startswith(('NGQA', 'Icon')):
            continue
        if el.find('.//' + A + 'blip') is None:
            continue
        out[el] = k
        k += 1
    return out


def next_num(i):
    for j in range(i + 1, min(i + 4, len(slides) + 1)):
        t = etree.fromstring(parts['ppt/' + slides[j - 1]])
        cls, te, ne, rest = classify(t)
        _, num = title_parts(t, te, ne)
        if num:
            return num
    return ''


def agenda_items_from_text(el):
    items = []
    k = 0
    for p in el.iter(A + 'p'):
        s = ''.join(x.text or '' for x in p.iter(A + 't')).strip()
        if not s:
            continue
        ppr = p.find(A + 'pPr')
        auto = ppr is not None and ppr.find(A + 'buAutoNum') is not None
        m = re.match(r'^(\d+(?:\.\d+)*)\s*(.*)$', s)
        if m:
            items.append((m.group(1), m.group(2).strip()))
        elif auto:
            k += 1
            items.append((f'{k}.', s))
        else:
            items.append(('', s))
    return items


def agenda_lines(grps):
    items = []
    cur = None
    for g in sorted(grps, key=lambda e: box(e)[1]):
        segs = []
        for p in g.iter(A + 'p'):
            t_ = ''.join(x.text or '' for x in p.iter(A + 't')).strip()
            em = any(is_emph_color(color_of(r.find(A + 'rPr'))) for r in p.iter(A + 'r') if (r.findtext(A + 't') or '').strip())
            if t_ and t_ != '|':
                segs.append((t_, em))
        pend = ''
        for t_, em in segs:
            m = re.match(r'^(\d+(?:\.\d+)+)\s*(.*)$', t_)
            if NUMRE.match(t_):
                if items and items[-1][0] == '' :
                    items[-1] = (t_.strip(), items[-1][1])
                else:
                    pend = t_.strip()
                continue
            if m and m.group(2):
                items.append((m.group(1), m.group(2)))
            else:
                items.append((pend, t_))
                pend = ''
            if em:
                cur = len(items) - 1
    if not items or len(items) > 14:
        return None
    return items, cur


report = []
counter = {}
last = None
for i, s in enumerate(slides, 1):
    if i <= 2:
        continue
    name = 'ppt/' + s
    t = etree.fromstring(parts[name])
    tr = t.find('.//' + P + 'spTree')
    if any((x.get('name') or '').startswith('NGQA Logo') and box(x.getparent().getparent()) and box(x.getparent().getparent())[2] > 2.5
           for x in tr.iter(P + 'cNvPr')):
        report.append((i, 'cover', ''))
        continue
    cls, tel, nel, rest = classify(t)
    for k_, e_ in list(rest):
        ph_ = e_.find('.//' + P + 'ph')
        if ph_ is not None and ph_.get('type') in ('sldNum', 'ftr', 'dt'):
            e_.getparent().remove(e_)
            rest.remove((k_, e_))
            continue
        b_ = box(e_)
        if k_ in ('textplain', 'boxed') and b_ and ((re.match(r'^\s*\d{1,3}\s*$', text(e_)) and b_[2] < 1.3) or
                                                    (re.match(r'^\s*פרק\s*\d+\s+\S+(\s+\S+)?\s*$', text(e_)) and b_[1] > H - 1.6)):
            e_.getparent().remove(e_)
            rest.remove((k_, e_))
    kinds_ = [k for k, _ in rest]
    if cls == 'complex' and all(k in ('textplain', 'pic', 'icon') for k in kinds_) and kinds_.count('textplain') <= 3 and kinds_.count('pic') <= 2:
        cls = 'simple'
    tk, num = title_parts(t, tel, nel)
    title = tk[0]
    labels = label_pics(tr)
    ids = Ids(max_id(t) + 10)
    new = []
    kinds = [k for k, _ in rest]
    body_text = ' '.join(text(e) for _, e in rest)
    ctx = {'title': title, 'body': body_text, 'counter': counter}
    used = None
    # --- agenda with marker ---
    tps = [e for k, e in rest if k == 'textplain']
    marker = [e for k, e in rest if k == 'shape' and box(e) and box(e)[2] < 1.0 and box(e)[0] > W * 0.7]
    grps = [e for k, e in rest if k == 'grp']
    if len(tps) == 1 and len(marker) == 1 and len(rest) == 2:
        items = agenda_items_from_text(tps[0])
        nn = next_num(i)
        cur = None
        for k2, (a, b) in enumerate(items):
            if a and nn and (nn == a or nn.startswith(a + '.')):
                cur = k2
        _ov = json.load(open('agenda_cur.json')).get(f'{N}-{i}')
        if isinstance(_ov, dict):
            ctx['bignum'], ctx['head'], ctx['kicker'] = _ov['num'], _ov['head'], 'הנושא הבא'
            cur = -1
        elif _ov is not None:
            cur = _ov
        if cur is None:
            # estimate from marker position
            b0 = box(tps[0]); mb = box(marker[0])
            frac = (mb[1] + mb[3] / 2 - b0[1]) / b0[3]
            cur = max(0, min(len(items) - 1, int(frac * len(items))))
        new = L_agenda(ids, s, ctx, items, None if cur == -1 else cur)
        used = 'agenda'
    elif grps and all(k in ('grp', 'textplain', 'shape') for k in kinds) and len(tps) <= 1 and \
            all(re.search(r'\d+(\.\d+)+', text(g)) for g in grps) and agenda_lines(grps) is not None:
        items, cur = agenda_lines(grps)
        head = text(tps[0]) if tps else title
        ctx['head'] = head
        ctx['kicker'] = 'פרק ' + str(N) if 'נלמד' in head else ''
        ctx['bignum'] = ''
        if 'נלמד' not in head:
            m = re.search(r'(\d+(\.\d+)*)', head)
            ctx['bignum'] = m.group(1) if m else ''
            ctx['head'] = next((b for a, b in items if a == ctx['bignum']), '') or re.sub(r'(פרק\s*)?\d+(\.\d+)*', '', head).strip() or title
            if cur is None:
                ctx['kicker'] = 'פרק ' + ctx['bignum'] if ctx['bignum'] else ''
        new = L_agenda(ids, s, ctx, items, cur)
        used = 'agenda2'
    elif cls == 'cards':
        tiles = []
        intro = []
        for k, e in rest:
            ps = [x for x in extract_paras([e]) if x]
            if k == 'boxed':
                tiles.append((box(e), ps))
            else:
                intro += ps
        # reading order: rows top->bottom, right->left
        tiles.sort(key=lambda b: (round(b[0][1] * 2), -b[0][0]))
        new = L_tiles(ids, s, ctx, [p for _, p in tiles], intro)
        used = 'tiles' if new else None
        if not new:
            cls = 'complex'
            new = []
    if used is None and cls == 'simple':
        pics = [e for k, e in rest if k == 'pic']
        figs = []
        for e in pics:
            lab = f'{N}-{i}-{labels.get(e, -1)}'
            if lab in CONTENT:
                fn = redraw.get(lab)
                if fn:
                    figs.append(fn)
                else:
                    rid = e.find('.//' + A + 'blip').get(R + 'embed')
                    figs.append(frame_fig(s, rid, e.find('.//' + P + 'cNvPr').get('descr') or ''))
        ms, groups = analyse(extract_paras(tps))
        ctx['ms'] = ms
        ctx['groups'] = groups
        if figs:
            new = L_figure(ids, s, ctx, figs)
            used = 'figure'
        elif ms:
            used, new = choose(ids, s, ctx, last)
        else:
            used, new = 'empty', []
    if used is None:
        # complex: keep geometry, restyle
        used = 'restyle'
        keep = []
        for k, e in rest:
            if k == 'pic':
                lab = f'{N}-{i}-{labels.get(e, -1)}'
                b = box(e)
                fn = redraw.get(lab) if lab in CONTENT else None
                if lab in CONTENT:
                    if fn and e.getparent() is tr and b:
                        bx0, by0 = max(b[0], X0 - 0.3), max(b[1], Y0 - 0.1)
                        bx1, by1 = min(b[0] + b[2], X1 + 0.3), min(b[1] + b[3], Y1)
                        new += fn(ids, bx0, by0, bx1 - bx0, by1 - by0)
                        tr.remove(e)
                    else:
                        sppr = e.find(P + 'spPr')
                        if sppr.find(A + 'ln') is None:
                            sppr.append(frag(f'<a:ln xmlns:a="{NSA}" w="9525">{solid(LINE)}</a:ln>'))
                    continue
                if b:
                    rid = illus(s, title, body_text)
                    sq = min(b[2], b[3])
                    new.append(pic_xml(ids, rid, b[0] + (b[2] - sq) / 2, b[1] + (b[3] - sq) / 2, sq, sq))
                    tr.remove(e)
                continue
            # pictures nested in groups
            if k == 'grp':
                for pe in list(e.iter(P + 'pic')):
                    lab = f'{N}-{i}-{labels.get(pe, -1)}'
                    if pe in labels and lab not in CONTENT:
                        rid = illus(s, title, body_text)
                        pe.find('.//' + A + 'blip').set(R + 'embed', rid)
                        xf = pe.find(P + 'spPr/' + A + 'xfrm')
                        o, ex = xf.find(A + 'off'), xf.find(A + 'ext')
                        cx, cy = int(ex.get('cx')), int(ex.get('cy'))
                        sq = min(cx, cy)
                        o.set('x', str(int(o.get('x')) + (cx - sq) // 2)); o.set('y', str(int(o.get('y')) + (cy - sq) // 2))
                        ex.set('cx', str(sq)); ex.set('cy', str(sq))
                        sr = pe.find('.//' + A + 'srcRect')
                        if sr is not None:
                            sr.getparent().remove(sr)
            recolor_tree(e)
            round_boxes(e)
            for sp in e.iter(P + 'sp'):
                fix_contrast(sp)
            for gf in e.iter(P + 'graphicFrame'):
                restyle_table(gf)
        # charts / smartart parts
        rm = slide_rel_map(s)
        for rid, tg in rm.items():
            if 'charts/' in tg or 'diagrams/' in tg:
                recolor_part(os.path.normpath(os.path.join('ppt/slides', tg)).replace('\\', '/'))
    # remove title elements
    for e in tel + nel:
        if e.getparent() is not None:
            e.getparent().remove(e)
    if used not in ('restyle',):
        for k, e in rest:
            if e.getparent() is not None:
                e.getparent().remove(e)
    elif True:
        for k, e in rest:
            if k == 'icon' and e.getparent() is not None:
                e.getparent().remove(e)
    els = (build_title(ids, tk, num) if title else []) + new
    for x in els:
        if x is None:
            continue
        tr.append(frag(x) if isinstance(x, str) else x)
    tm = t.find(P + 'timing')
    if tm is not None:
        have = {x.get('id') for x in t.iter(P + 'cNvPr')}
        if any(x.get('spid') not in have for x in tm.iter(P + 'spTgt')):
            t.remove(tm)
    parts[name] = etree.tostring(t, xml_declaration=True, encoding='UTF-8', standalone=True)
    report.append((i, used, title[:40]))
    if used not in ('restyle',):
        last = used

with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n in parts:
        zo.writestr(n, parts[n])
from collections import Counter
print(Counter(u for _, u, _ in report))
json.dump(report, open(f'v2_report_{N}.json', 'w'), ensure_ascii=False)
