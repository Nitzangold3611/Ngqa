#!/bin/bash
# full rebuild from d{n}_new.pptx (restyled) to d{n}_final.pptx
set -eo pipefail
cd /home/claude/work
r(){ seq -s, $1 $2; }
DEL1=11,25,26,27,36,37,82,83,94,95
DEL2=104,105,106,139,185,186,187,188
DEL3=10,39
DEL5=$(r 49 54),$(r 80 84),$(r 105 108),$(r 119 124),$(r 138 143)
for n in 1 2 3 4 5 6; do
  python3 fix_titles.py d${n}_new.pptx d${n}_fix.pptx > log_t$n.txt; head -1 log_t$n.txt
  python3 fix_smartart.py d${n}_fix.pptx d${n}_fix2.pptx > log_s$n.txt; tail -1 log_s$n.txt
done
# chapter 1, old slide 60: move the red/green labels clear of the list
rm -rf xs && mkdir xs && (cd xs && unzip -q ../d1_fix2.pptx && python3 - <<'P'
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}';Pn='{http://schemas.openxmlformats.org/presentationml/2006/main}'
f='ppt/slides/slide60.xml'; t=etree.parse(f)
for sp in t.getroot().iter(Pn+'sp'):
    if ''.join(sp.itertext()).strip() in ('שלילי (לא ולידי)','חיובי (ולידי)'):
        off=sp.find(Pn+'spPr/'+A+'xfrm/'+A+'off'); off.set('x',str(int(off.get('x'))-int(0.72*914400)))
t.write(f,xml_declaration=True,encoding='UTF-8',standalone=True)
P
rm -f ../d1_fix2.pptx && zip -qXrDy ../d1_fix2.pptx .)
for n in 1 2 3 4 5 6; do python3 fix_overflow.py d${n}_fix2.pptx d${n}_fix3.pptx > log_o$n.txt; cut -c1-50 log_o$n.txt; done
python3 delq.py d1_fix3.pptx d1_q.pptx $DEL1
python3 delq.py d2_fix3.pptx d2_q.pptx $DEL2
python3 delq.py d3_fix3.pptx d3_q.pptx $DEL3
cp d4_fix3.pptx d4_q.pptx
python3 delq.py d5_fix3.pptx d5_q.pptx $DEL5
cp d6_fix3.pptx d6_q.pptx
for n in 1 2 3 4 5 6; do python3 fix_icons.py d${n}_q.pptx d${n}_final.pptx & done; wait
python3 patch_d2.py d2_final.pptx d2_final_p.pptx && mv d2_final_p.pptx d2_final.pptx
python3 patch_d4.py d4_final.pptx d4_final_p.pptx && mv d4_final_p.pptx d4_final.pptx
python3 patch_d5.py d5_final.pptx d5_final_p.pptx && mv d5_final_p.pptx d5_final.pptx
for n in 1 2 3 4 5 6; do python3 add_toc.py $n d${n}_final.pptx d${n}_toc.pptx; done
# user feedback fixes (20.11.2026) + dark-text-on-dark-fill fix
for n in 1 2 3 4 5 6; do python3 patches2.py $n d${n}_toc.pptx d${n}_tp.pptx && python3 fix_contrast.py d${n}_tp.pptx d${n}_toc.pptx && rm d${n}_tp.pptx; done
S=/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx
for n in 1 2 3 4 5 6; do python3 $S/scripts/office/validate.py d${n}_toc.pptx --original d$n.pptx 2>&1 | tail -1; done
for n in 1 2 3 4 5 6; do (rm -rf hr$n && mkdir -p hr$n && cd hr$n && cp ../d${n}_toc.pptx deck.pptx && timeout 900 python3 $S/scripts/office/soffice.py --headless --convert-to pdf deck.pptx >/dev/null 2>&1; pdftoppm -jpeg -r 120 deck.pdf s) & done; wait
