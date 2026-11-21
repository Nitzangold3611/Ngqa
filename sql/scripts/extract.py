#!/usr/bin/env python3
"""Extract a per-slide content model from the original SQL deck -> model.json"""
import json, re, hashlib, os
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER

SRC = '/home/claude/sql/src.pptx'
IMG = '/home/claude/sql/imgs'
KEEP = set('050648a3 12898e46 1688e7fe 1ebc468c 360a0256 3cf4b44b 417402cc 436076c9 4d9ea6bf 51b3166c 53dd40d0 '
           '5b5d8c72 75f6d1a9 7984d321 7fae03d6 896235e7 982b9e8f a5004be6 b3a74ee7 c381630c c8b77347 c9d65fea '
           'd4f100e8 d6823ea1 e94f7c05 ee0bdc6f ef696940 7857f1b9'.split())
HEB = re.compile(r'[֐-׿]')
KW = re.compile(r'^\s*(SELECT|FROM|WHERE|ORDER|GROUP|HAVING|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|VALUES|SET|AND|OR|'
                r'INNER|LEFT|RIGHT|FULL|CROSS|JOIN|ON|UNION|EXEC|EXECUTE|DECLARE|BEGIN|END|AS|IF|ELSE|RETURN|INTO|'
                r'TRUNCATE|USE|GO|WITH|CASE|WHEN|THEN|PRINT|CONSTRAINT|PRIMARY|FOREIGN|REFERENCES|ADD|TOP|'
                r'EXCEPT|INTERSECT|BETWEEN|NOT|IN|LIKE|IS|NULL|SUM|AVG|COUNT|MIN|MAX)\b', re.I)


def clean(t):
    return t.replace('\x0b', '\n').replace('‏', '').replace('‎', '').rstrip()


def is_code(t):
    s = t.strip()
    if not s:
        return False
    if KW.match(s):
        # a prose line that only starts with a keyword?
        heb = len(HEB.findall(s))
        return heb <= 12 or '<' in s
    if HEB.search(s):
        return False
    # english-only line that looks like code
    return bool(re.search(r"[=;(),*\[\]']|^\w+\.\w+|^[A-Z0-9_]+(\s+[A-Z0-9_\[\]]+)*$", s)) and len(s) < 120


def pic_hash(sh):
    try:
        b = sh.image.blob
    except Exception:
        return None
    return hashlib.md5(b).hexdigest()[:8]


def walk(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(sh.shapes)
        else:
            yield sh


def model():
    p = Presentation(SRC)
    out = []
    for n, s in enumerate(p.slides, 1):
        m = {'n': n, 't': '', 't2': '', 'body': [], 'notes': [], 'tables': [], 'imgs': [], 'arrows': 0}
        shapes = list(walk(s.shapes))
        # reading order: top-to-bottom, right-to-left
        shapes.sort(key=lambda sh: ((sh.top or 0) // 300000, -(sh.left or 0)))
        for sh in shapes:
            if sh.is_placeholder:
                pt = sh.placeholder_format.type
                if pt in (PP_PLACEHOLDER.FOOTER, PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.DATE):
                    continue
                if pt in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
                    lines = [l.strip() for l in clean(sh.text_frame.text).split('\n') if l.strip()]
                    m['t'] = lines[0] if lines else ''
                    m['t2'] = ' '.join(lines[1:])
                    continue
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                h = pic_hash(sh)
                if h in KEEP:
                    f = next((x for x in os.listdir(IMG) if x.startswith(h)), None)
                    m['imgs'].append({'h': h, 'f': f, 'w': sh.width / 914400, 'hh': sh.height / 914400,
                                      'x': sh.left / 914400, 'y': sh.top / 914400})
                continue
            if getattr(sh, 'has_table', False) and sh.has_table:
                rows = [[clean(c.text).replace('\n', ' ') for c in r.cells] for r in sh.table.rows]
                m['tables'].append({'rows': rows, 'x': sh.left / 914400, 'w': sh.width / 914400})
                continue
            if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and 'Arrow' in sh.name:
                m['arrows'] += 1
                if sh.left / 914400 > 10:
                    m['agenda_arrow_y'] = sh.top / 914400
            if not sh.has_text_frame:
                continue
            paras = []
            for pa in sh.text_frame.paragraphs:
                t = clean(pa.text)
                bold = any(r.font.bold for r in pa.runs if r.text.strip())
                paras.append({'t': t.strip(), 'raw': t, 'lvl': pa.level, 'b': bold})
            if not any(x['t'] for x in paras):
                continue
            main = sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.OBJECT, PP_PLACEHOLDER.BODY,
                                                                           PP_PLACEHOLDER.SUBTITLE)
            (m['body'] if main else m['notes']).append({'paras': paras, 'x': sh.left / 914400, 'y': sh.top / 914400,
                                                        'w': sh.width / 914400, 'shape': sh.name})
        out.append(m)
    return out


if __name__ == '__main__':
    d = model()
    json.dump(d, open('/home/claude/sql/model.json', 'w'), ensure_ascii=False, indent=0)
    print(len(d), 'slides;', sum(len(x['imgs']) for x in d), 'kept images;', sum(len(x['tables']) for x in d), 'tables')
