
# ================================================================ SQL course additions
from lay import block_height
from PIL import Image as _PILImage

SQLKW = set('''SELECT FROM WHERE ORDER BY GROUP HAVING INSERT INTO VALUES UPDATE SET DELETE CREATE ALTER DROP TABLE VIEW
PROCEDURE PROC DATABASE INDEX AND OR NOT IN LIKE BETWEEN IS NULL AS ON JOIN INNER LEFT RIGHT FULL OUTER CROSS UNION ALL
DISTINCT TOP ASC DESC EXISTS ANY SOME CASE WHEN THEN ELSE END BEGIN DECLARE EXEC EXECUTE RETURN IF WHILE PRINT
PRIMARY KEY FOREIGN REFERENCES CONSTRAINT DEFAULT CHECK UNIQUE IDENTITY ADD COLUMN TRUNCATE USE GO WITH OUTPUT
INTERSECT EXCEPT INT VARCHAR NVARCHAR CHAR NCHAR DATETIME DATE MONEY DECIMAL NUMERIC FLOAT BIT TEXT SMALLINT
TINYINT BIGINT REAL ROWCOUNT PERCENT TIES OVER PARTITION CASCADE GRANT REVOKE COMMIT ROLLBACK TRANSACTION TRAN'''.split())
C_KW, C_STR, C_NUM, C_COM, C_FN, C_TXT = '14DACD', 'F7B267', 'B5E8A0', '8A93A6', 'FFD580', 'FFFFFF'


def sql_runs(ln, pt):
    if heb(ln) and not re.match(r'^\s*[A-Za-z]', ln):
        return run(ln, pt, C_TXT, False, 'Arial')
    out = []
    i = 0
    toks = re.findall(r"--.*$|'[^']*'?|\[[^\]]*\]?|\d+(?:\.\d+)?|[A-Za-z_@#][\w@#$]*|[֐-׿][֐-׿\"'׳״\s/\-]*|\s+|.", ln)
    for k, t in enumerate(toks):
        if t.startswith('--'):
            out.append(run(t, pt, C_COM, False, MONO, i=True))
        elif t.startswith("'"):
            out.append(run(t, pt, C_STR, False, MONO))
        elif re.match(r'^\d', t):
            out.append(run(t, pt, C_NUM, False, MONO))
        elif heb(t):
            out.append(run(t, pt, C_STR, False, 'Arial'))
        elif t.upper() in SQLKW:
            out.append(run(t, pt, C_KW, True, MONO))
        elif re.match(r'^[A-Za-z_]\w*$', t) and k + 1 < len(toks) and toks[k + 1] == '(':
            out.append(run(t, pt, C_FN, False, MONO))
        else:
            out.append(run(t, pt, C_TXT, False, MONO))
    return ''.join(out)


def code_lines(code, pt, iw):
    return sum(max(1, math.ceil(wlen(l, pt, 0) * 1.3 / iw)) for l in code.split('\n'))


def code_need(code, w, pt):
    n = code_lines(code, pt, w - 0.5)
    return n * pt * 1.3 / 72 + (0.62 if n > 2 else 0.3)


def sql_panel(s, x, y, w, h, code, pt):
    lines = code.split('\n')
    small = len(lines) <= 2
    s.rect(x, y, w, h, NAVY, 'roundRect', {'adj': 4000}, name='Code Panel')
    if not small:
        for k, c in enumerate(('E0475B', 'F3B811', '12A37A')):
            s.rect(x + 0.2 + k * 0.22, y + 0.16, 0.14, 0.14, c, 'ellipse')
        s.text('SQL', x + w - 0.75, y + 0.06, 0.55, 0.3, 10, 'A9B1C2', True, 'r')
    body = ''.join(f'<a:p><a:pPr algn="l" rtl="0"/>{sql_runs(ln, pt) if ln.strip() else ""}'
                   f'<a:endParaRPr lang="en-US" sz="{int(pt * 100)}"/></a:p>' for ln in lines)
    top = 0.1 if small else 0.44
    s.add(sp_xml(s.ids, 'Code', x + 0.25, y + top, w - 0.4, h - top - 0.08, 'rect', body=body, anchor='ctr',
                 ins=(0.02, 0.02, 0.02, 0.02), txbox=True))


def items_h(items, w, pt):
    if not items:
        return 0
    return block_height(meas(items), w * 0.96, pt, 0.42) + 0.1


def tbl_layout(rows, w, h, maxpt=16):
    nc = max(len(r) for r in rows)
    rows = [r + [''] * (nc - len(r)) for r in rows]
    pt = maxpt
    while True:
        b0 = lambda i: i == 0
        nat = [max(wlen(r[j], pt, b0(i)) for i, r in enumerate(rows)) * 1.08 + 0.3 for j in range(nc)]
        mn = [max([wlen(wd, pt, b0(i)) for i, r in enumerate(rows) for wd in r[j].split()] or [0.2]) * 1.08 + 0.3 for j in range(nc)]
        nat = [min(n, max(m, 3.4)) for n, m in zip(nat, mn)]
        cw = nat[:]
        if sum(cw) > w:
            extra = sum(nat) - w
            slack = sum(n - m for n, m in zip(nat, mn))
            if slack >= extra and slack > 0:
                cw = [n - (n - m) * extra / slack for n, m in zip(nat, mn)]
            else:
                cw = None
        if cw:
            rh = []
            for i, r in enumerate(rows):
                m = 1
                for j, t in enumerate(r):
                    m = max(m, math.ceil(wlen(t, pt, i == 0) * 1.06 / max(0.2, cw[j] - 0.18) - 0.02))
                rh.append(m * pt * 1.25 / 72 + 0.12)
            if sum(rh) <= h or pt <= 8:
                return rows, cw, rh, pt
        elif pt <= 8:
            cw = [w / nc] * nc
            rh = [pt * 2.6 / 72 + 0.12] * len(rows)
            return rows, cw, rh, pt
        pt -= 0.5


def tbl(s, x, y, w, h, rows, maxpt=16):
    """data table; returns used height"""
    rows, cw, rh, pt = tbl_layout(rows, w, h, maxpt)
    need_w = sum(cw)
    x0 = x + (w - need_w) / 2
    yy = y
    hebrow = any(heb(t) for r in rows for t in r)
    for i, r in enumerate(rows):
        xx = x0 + need_w if hebrow else x0
        for j, t in enumerate(r):
            if hebrow:
                xx -= cw[j]
                cx = xx
            else:
                cx = xx
                xx += cw[j]
            if i == 0:
                fill, col, b = NAVY, 'FFFFFF', True
            else:
                fill, col, b = ('FFFFFF' if i % 2 else 'F4F6FA'), BODY, False
            t2 = t.strip()
            if t2 in ('NULL', '<NULL>'):
                col = GRAY
            body = P(t2, pt, col, b, 'ctr', rtl=heb(t2)) if t2 else ''
            s.add(sp_xml(s.ids, 'Cell', cx, yy, cw[j], rh[i], 'rect', fill=fill, line=LINE, lw=0.75, body=body,
                         anchor='ctr', ins=(0.06, 0.02, 0.06, 0.02), txbox=True))
        yy += rh[i]
    return yy - y


def tbl_need(rows, w, pt=12):
    rows, cw, rh, pt = tbl_layout(rows, w, 99, pt)
    return sum(rh), sum(cw)


def img_place(s, path, x, y, w, h):
    im = _PILImage.open(path)
    ar = im.width / im.height
    if w / h > ar:
        iw, ih = h * ar, h
    else:
        iw, ih = w, w / ar
    ix, iy = x + (w - iw) / 2, y + (h - ih) / 2
    s.rect(ix - 0.06, iy - 0.06, iw + 0.12, ih + 0.12, 'FFFFFF', 'roundRect', {'adj': 3000}, line=LINE, lw=1,
           name='Image Frame')
    s.add(pic_xml(s.ids, s.media(path), ix, iy, iw, ih, name='Screenshot', descr=os.path.basename(path)))
    return ih + 0.12


def callout(s, x, y, w, h, items, pt):
    s.rect(x, y, w, h, 'FFF6EA', 'roundRect', {'adj': 14000}, name='Callout')
    s.rect(x + w - 0.07, y + 0.08, 0.07, h - 0.16, ORANGE, name='Callout Bar')
    s.box('Callout Text', x + 0.15, y, w - 0.35, h, items, pt=pt, al='r', anchor='ctr', ins=(0.04, 0.03, 0.04, 0.03))


def L_auto(s, sp, top):
    flow = sp['flow']
    bottom = 6.74
    texts = [f for f in flow if f[0] in ('p', 'code', 'note', 'pills', 'venn')]
    vis = [f for f in flow if f[0] in ('table', 'img')]
    avail = bottom - top
    gap = 0.16
    mode = 'full'
    if vis and texts:
        wide = any((f[0] == 'table' and (len(f[1][0]) >= 5 or tbl_need(f[1], 99, 13)[1] > 5.0)) or
                   (f[0] == 'img' and f[2] > 1.5) for f in vis)
        mode = 'stack' if wide else 'side'
    elif vis:
        mode = 'visonly'
    if mode == 'side':
        tw = 6.9
        tx = X1 - tw
        vx, vw = X0, X1 - tw - X0 - 0.35
    else:
        tx, tw = X0 + 0.35, X1 - X0 - 0.35
        vx, vw = X0, X1 - X0

    def heights(pt, w):
        hs = []
        for f in texts:
            if f[0] == 'p':
                hs.append(items_h(f[1], w, pt))
            elif f[0] == 'note':
                hs.append(items_h(f[1], w - 0.5, pt * 0.92) + 0.12)
            elif f[0] == 'pills':
                hs.append(0.46)
            elif f[0] == 'venn':
                hs.append(1.7)
            else:
                hs.append(code_need(f[1], w, min(pt - 3, 18)))
        return hs

    vis_min = 0
    if mode == 'stack':
        vis_need = sum(tbl_need(f[1], vw, 11)[0] if f[0] == 'table' else 2.6 for f in vis) + gap * (len(vis) - 1)
        vis_min = min(max(0.9, vis_need + 0.1), avail * 0.62)
    tav = avail - vis_min - (0.25 if vis_min else 0)
    pt = 24
    while pt > 11:
        hs = heights(pt, tw)
        if sum(hs) + gap * (len(hs) - 1) <= tav:
            break
        pt -= 0.5
    hs = heights(pt, tw)
    used = sum(hs) + gap * (len(hs) - 1) if hs else 0
    y = top + (max(0, tav - used) * (0.35 if mode in ('full', 'side') else 0.0) if texts else 0)
    if mode == 'side' and texts:
        y = top + max(0, tav - used) * 0.3
    for f, h in zip(texts, hs):
        if f[0] == 'p':
            s.box('Body', tx, y, tw, h, f[1], pt=pt, al='r', anchor='t', ins=(0.02, 0.02, 0.02, 0.02))
        elif f[0] == 'note':
            callout(s, tx, y, tw, h, f[1], pt * 0.92)
        elif f[0] == 'pills':
            pills(s, f[1], tx, y, tw, 0.4, 14, al='r')
        elif f[0] == 'venn':
            venn2(s, tx + tw - 3.4, y, 3.2, h, f[1])
        else:
            cpt = min(pt - 3, 18)
            cw = tw
            # narrow code panel to its content
            longest = max(wlen(l, cpt, 0) for l in f[1].split('\n')) * 1.3 + 0.8
            cw = min(tw, max(3.6, longest))
            sql_panel(s, tx + tw - cw if True else tx, y, cw, h, f[1], cpt)
        y += h + gap
    # visuals
    if not vis:
        return
    if mode == 'side':
        vy, vh = top, avail
    elif mode == 'visonly':
        vy, vh = top, avail
    else:
        vy = y + 0.1 if texts else top
        vh = bottom - vy
    tables = [f for f in vis if f[0] == 'table']
    horiz = len(vis) > 1 and all(f[0] == 'table' for f in vis) and mode in ('stack', 'visonly') and \
        sum(tbl_need(f[1], vw, 9)[1] for f in vis) + 0.5 * (len(vis) - 1) <= vw
    if horiz:
        ws = [tbl_need(f[1], vw, 11)[1] for f in vis]
        sc = min(1.0, (vw - 0.5 * (len(vis) - 1)) / sum(ws))
        xx = vx + vw
        for f, w_ in zip(vis, ws):
            w_ *= sc
            xx -= w_
            tbl(s, xx, vy, w_ + 0.0, vh, f[1], 16)
            xx -= 0.5
        return
    if len(vis) == 1 and vis[0][0] == 'table':
        rows_, cw_, rh_, pt_ = tbl_layout(vis[0][1], vw, vh, 18 if mode != 'stack' else 16)
        used_ = sum(rh_)
        tbl(s, vx, vy + (max(0, vh - used_) * (0.4 if mode != 'stack' else 0.0)), vw, vh, vis[0][1],
            18 if mode != 'stack' else 16)
        return
    needs = []
    for f in vis:
        if f[0] == 'table':
            needs.append(tbl_need(f[1], vw, 12)[0])
        else:
            needs.append(min(vh, vw / f[2], (vh - gap * (len(vis) - 1)) / len(vis)))
    tot = sum(needs) + gap * (len(vis) - 1)
    sc = min(1.0, (vh - gap * (len(vis) - 1)) / max(0.1, sum(needs)))
    yy = vy + (max(0, vh - tot) / 2 if mode != 'stack' else 0)
    for f, nh in zip(vis, needs):
        hh = nh * sc if sc < 1 else nh
        if f[0] == 'table':
            used_h = tbl(s, vx, yy, vw, hh if sc < 1 else vh - (yy - vy), f[1], 14)
            yy += used_h + gap
        else:
            img_place(s, f[1], vx, yy, vw, hh)
            yy += hh + gap


LAY['auto'] = L_auto


_L_section0 = L_section


def L_section2(s, sp):
    _L_section0(s, sp)
    tp = sp.get('topics')
    if not tp:
        return
    x0 = X0 + 4.4 + 0.5
    cur = sp.get('cur', 1)
    y = 3.35
    rh = min(0.62, (6.6 - y) / len(tp))
    for k, t in enumerate(tp, 1):
        on = k == cur
        s.box('Topic', x0, y, X1 - x0, rh - 0.1, [(f'{sp["k"].split(".")[0]}.{k}   {t}', 'h' if on else 'x')],
              pt=16 if on else 15, al='r', anchor='ctr', fill=TINT if on else 'FFFFFF', line=TEAL if on else LINE,
              lw=1.5 if on else 0.75, col=GRAY, hcol=NAVY, ins=(0.15, 0.02, 0.2, 0.02))
        if on:
            s.rect(X1 - 0.08, y + 0.06, 0.08, rh - 0.22, ORANGE)
        y += rh


L_section = L_section2


def venn2(s, x, y, w, h, kind):
    d = min(h - 0.35, w * 0.6)
    x = x + w - d * 1.6
    w = d * 1.6
    cy = y + 0.02
    xa = x                  # table A on the left (as in LEFT JOIN)
    xb = x + w - d
    on = {'inner': (False, False), 'left': (True, False), 'right': (False, True), 'full': (True, True),
          'all': (False, False)}[kind]
    # left join keeps the first (left-hand) table = A
    for xx, solid_ in ((xa, on[0]), (xb, on[1])):
        s.rect(xx, cy, d, d, TEAL if solid_ else 'FFFFFF', 'ellipse', line=TEAL_D, lw=1.5,
               alpha=55000 if solid_ else None, name='Venn')
    if kind == 'inner':
        # overlap highlight
        ox = xb + d - (d - (w - d)) if False else xa
        ow = xa + d - xb
        if ow > 0:
            s.rect(xb + ow * 0.12, cy + d * 0.18, ow * 0.76, d * 0.64, ORANGE, 'ellipse', alpha=80000, name='Venn Overlap')
    s.text("טבלה א'", xa, cy + d + 0.02, d, 0.3, 12, NAVY, True, 'ctr')
    s.text("טבלה ב'", xb, cy + d + 0.02, d, 0.3, 12, NAVY, True, 'ctr')


def _stem_lines(st):
    import re as _re
    out = []; k = 0
    for t in st:
        if _re.match(r'^[A-Z] — ', t):
            out.append((t, 'x'))
        else:
            k += 1; out.append((f'{k}. ' + t, 'x'))
    return out


def L_mcq(s, sp, top):
    """Exam question slide. sp: q, opts[], ans (list of indices) optional, pick, topic, exp."""
    letters = ['א', 'ב', 'ג', 'ד', 'ה', 'ו']
    ans = sp.get('ans')
    bottom = 6.78
    if sp.get('exp') and ans is not None:
        bottom -= 0.66
        s.box('Explanation', X0, bottom + 0.1, X1 - X0, 0.58, [('💡 הסבר: ' + sp['exp'], 'h')], 15, 10, al='r',
              anchor='ctr', fill='FFF4E8', line=ORANGE, ins=(0.2, 0.02, 0.2, 0.02))
    pick = sp.get('pick', 'בחרו תשובה אחת')
    s.box('Pick', X0 + 1.5, top - 0.5, 3.0, 0.34, [(('✓ ' if ans is not None else '✦ ') + pick, 'h')], pt=13, al='ctr',
          anchor='ctr', fill=ORANGE if ans is None else TEAL, hcol='FFFFFF', adj={'adj': 50000}, ins=(0.02, 0, 0.02, 0))
    # question
    qh = 0.8 if len(sp['q']) < 90 else (1.05 if len(sp['q']) < 170 else 1.3)
    s.box('Question', X0, top, X1 - X0, qh, [(sp['q'], 'h')], 20, 12, al='r', anchor='ctr', fill=TINT, line=None,
          ins=(0.3, 0.05, 0.3, 0.05))
    s.rect(X1 - 0.08, top, 0.08, qh, TEAL)
    y0 = top + qh + 0.2
    if sp.get('stem'):
        sh = 0.31 * len(sp['stem']) + 0.16
        s.box('Stem', X0 + 0.4, y0, X1 - X0 - 0.4, sh, _stem_lines(sp['stem']), 15, 10,
              al='r', anchor='ctr', fill='FFFFFF', line=LINE, ins=(0.3, 0.05, 0.3, 0.05))
        y0 += sh + 0.2
    opts = sp['opts']
    grid = len(opts) == 4 and max(len(o) for o in opts) < 70 and not sp.get('rows')
    gap = 0.18
    if grid:
        cw = (X1 - X0 - gap) / 2
        rh = min(1.35, (bottom - y0 - gap) / 2)
        pos = [(X1 - cw, y0), (X0, y0), (X1 - cw, y0 + rh + gap), (X0, y0 + rh + gap)]
        dims = [(cw, rh)] * 4
    else:
        rh = min(0.85, (bottom - y0 - gap * (len(opts) - 1)) / len(opts))
        pos = [(X0, y0 + k * (rh + gap)) for k in range(len(opts))]
        dims = [(X1 - X0, rh)] * len(opts)
    for k, o in enumerate(opts):
        x, y = pos[k]
        w, h = dims[k]
        ok = ans is not None and k in ans
        dim = ans is not None and not ok
        fill = 'E3F6F4' if ok else ('F4F5F8' if dim else 'FFFFFF')
        line = TEAL if ok else ('D9DCE3' if dim else LINE)
        s.rect(x, y, w, h, fill, 'roundRect', {'adj': 12000}, line=line, lw=2.5 if ok else 1)
        cc = TEAL if ok else (NAVY if not dim else 'B8BCC8')
        s.rect(x + w - 0.72, y + h / 2 - 0.27, 0.54, 0.54, cc, 'ellipse')
        s.text('✓' if ok else letters[k], x + w - 0.72, y + h / 2 - 0.27, 0.54, 0.54, 18 if ok else 16, 'FFFFFF', True, 'ctr')
        s.box('Option', x + 0.2, y, w - 1.1, h, [(o, 'h' if ok else 'x')], 17, 10, al='r', anchor='ctr',
              col='9AA0AE' if dim else BODY, hcol=TEAL_D, ins=(0.02, 0, 0.02, 0))


def L_mcq_why(s, sp, top):
    """Answer slide with an explanation for every option (sp['why'])."""
    letters = ['א', 'ב', 'ג', 'ד', 'ה', 'ו']
    ans = sp['ans']
    bottom = 6.8
    pick = sp.get('pick', 'בחרו תשובה אחת')
    s.box('Pick', X0 + 1.5, top - 0.5, 3.0, 0.34, [('✓ ' + pick, 'h')], pt=13, al='ctr', anchor='ctr', fill=TEAL,
          hcol='FFFFFF', adj={'adj': 50000}, ins=(0.02, 0, 0.02, 0))
    qh = 0.62 if len(sp['q']) < 120 else (0.85 if len(sp['q']) < 260 else 1.1)
    s.box('Question', X0, top, X1 - X0, qh, [(sp['q'], 'h')], 15, 9, al='r', anchor='ctr', fill=TINT, line=None,
          ins=(0.3, 0.04, 0.3, 0.04))
    s.rect(X1 - 0.08, top, 0.08, qh, TEAL)
    y0 = top + qh + 0.14
    opts = sp['opts']; why = sp['why']; n = len(opts); gap = 0.1
    wts = [(1.0 + (len(o) + len(why[k])) / 150) * (1.35 if k in ans else 1.0) for k, o in enumerate(opts)]
    avail = bottom - y0 - gap * (n - 1)
    pts = []
    y = y0
    for k, o in enumerate(opts):
        h = avail * wts[k] / sum(wts)
        ok = k in ans
        fill = 'E3F6F4' if ok else 'FFFFFF'
        s.rect(X0, y, X1 - X0, h, fill, 'roundRect', {'adj': 9000}, line=TEAL if ok else LINE, lw=2.25 if ok else 0.75)
        cc = TEAL if ok else 'B8BCC8'
        d = min(0.48, h - 0.12)
        s.rect(X1 - 0.66, y + h / 2 - d / 2, d, d, cc, 'ellipse')
        s.text('✓' if ok else letters[k], X1 - 0.66, y + h / 2 - d / 2, d, d, 15, 'FFFFFF', True, 'ctr')
        items = [(o, 'h' if ok else 'g'), (why[k], 'k' if ok else 'v')]
        pts.append(s.box('Option', X0 + 0.15, y, X1 - X0 - 0.95, h, items, 16, 9, al='r', anchor='ctr',
                         col=BODY, hcol=TEAL_D, ins=(0.06, 0.02, 0.04, 0.02), spacing=0.25))
        y += h + gap


_L_mcq_plain = L_mcq


def L_mcq(s, sp, top):
    if sp.get('why') and sp.get('ans') is not None:
        return L_mcq_why(s, sp, top)
    return _L_mcq_plain(s, sp, top)


LAY['mcq'] = L_mcq


_toc_entries_orig = toc_entries


def toc_entries(specs):
    ents = _toc_entries_orig(specs)
    if ents:
        return ents
    out = []
    for idx, sp in enumerate(specs, 1):
        if sp['L'] == 'mcq' and sp.get('ans') is None:
            out.append((0, str(len(out) + 1), sp['t'].split('— ', 1)[-1], idx))
    if out:
        return out
    seen = set()
    for idx, sp in enumerate(specs, 1):
        k = (sp.get('k') or '').split('·')[-1].strip()
        if sp['L'] == 'cover' or not k or k in seen:
            continue
        seen.add(k)
        out.append((0, str(len(out) + 1), k + ' — ' + sp['t'].split(':')[-1].strip(), idx))
    return out
