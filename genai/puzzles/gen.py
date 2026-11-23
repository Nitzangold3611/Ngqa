#!/usr/bin/env python3
"""Crossword layout generator (deterministic: fixed random seed). Outputs layout dicts for build.py."""
import random

def place_all(words, rnd, maxdim=19):
    words = sorted(words, key=lambda w: -len(w[0]))
    first, rest = words[0], words[1:]
    rnd.shuffle(rest)
    rest.sort(key=lambda w: -len(w[0]) + rnd.random() * 4)
    grid = {}; placed = []
    def put(w, r, c, d):
        for i, ch in enumerate(w):
            grid[(r + (d == 'D') * i, c + (d == 'A') * i)] = ch
    def ok(w, r, c, d):
        dr, dc = (1, 0) if d == 'D' else (0, 1)
        inter = 0
        if grid.get((r - dr, c - dc)) or grid.get((r + dr * len(w), c + dc * len(w))): return -1
        for i, ch in enumerate(w):
            p = (r + dr * i, c + dc * i); g = grid.get(p)
            if g:
                if g != ch: return -1
                inter += 1
            else:
                # no side neighbours for new cells
                s1 = (p[0] + dc, p[1] + dr); s2 = (p[0] - dc, p[1] - dr)
                if grid.get(s1) or grid.get(s2): return -1
        rs = [k[0] for k in grid] + [r, r + dr * (len(w) - 1)]
        cs = [k[1] for k in grid] + [c, c + dc * (len(w) - 1)]
        if max(rs) - min(rs) >= maxdim or max(cs) - min(cs) >= maxdim: return -1
        return inter
    put(first[0], 0, 0, 'A'); placed.append((first, 0, 0, 'A'))
    pending = list(rest)
    for _ in range(3):
        left = []
        for w in pending:
            best = None
            for (pr, pc), ch in list(grid.items()):
                for i, wc in enumerate(w[0]):
                    if wc != ch: continue
                    for d in 'AD':
                        r, c = (pr - i, pc) if d == 'D' else (pr, pc - i)
                        s = ok(w[0], r, c, d)
                        if s > 0 and (best is None or s + rnd.random() > best[0]):
                            best = (s + rnd.random(), r, c, d)
            if best: put(w[0], best[1], best[2], best[3]); placed.append((w, best[1], best[2], best[3]))
            else: left.append(w)
        pending = left
    return placed, grid, pending

def layout(words, tries=3000, seed=7, maxdim=19):
    rnd = random.Random(seed); best = None
    for _ in range(tries):
        placed, grid, left = place_all(list(words), rnd, maxdim)
        if left: continue
        rs = [k[0] for k in grid]; cs = [k[1] for k in grid]
        h, w = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
        inter = sum(len(p[0][0]) for p in placed) - len(grid)
        score = inter * 6 - h * w * 0.08 - abs(h - w)
        if best is None or score > best[0]:
            best = (score, placed, min(rs), min(cs), h, w)
    assert best, 'could not place all words'
    _, placed, r0, c0, H, W = best
    # numbering: reading order (rows top->bottom, columns right->left for an RTL page? the grid itself is LTR English)
    starts = {}
    for (w, r, c, d) in placed: starts.setdefault((r - r0, c - c0), []).append(d)
    nums = {}; k = 0
    for pos in sorted(starts): k += 1; nums[pos] = k
    entries = [dict(ans=w[0], clue=w[1], r=r - r0, c=c - c0, d=d, n=nums[(r - r0, c - c0)]) for (w, r, c, d) in placed]
    entries.sort(key=lambda e: (e['d'], e['n']))
    return dict(H=H, W=W, entries=entries)

if __name__ == '__main__':
    from words import CROSS, CRYPTIC
    for name, ws in (('cross', CROSS), ('cryptic', CRYPTIC)):
        L = layout(ws)
        g = [['.'] * L['W'] for _ in range(L['H'])]
        for e in L['entries']:
            for i, ch in enumerate(e['ans']):
                g[e['r'] + (e['d'] == 'D') * i][e['c'] + (e['d'] == 'A') * i] = ch
        print(name, L['H'], 'x', L['W']); print('\n'.join(' '.join(r) for r in g))
