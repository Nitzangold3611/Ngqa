#!/bin/bash
set -e
cd /home/claude/work
for n in ${@:-1 2 3 4 5 6}; do
  python3 relayout.py $n d${n}_toc_v1.pptx b_$n.pptx > /dev/null
  python3 fix_nowrap.py $n b_$n.pptx b2_$n.pptx > /dev/null
  python3 patches.py $n b2_$n.pptx b3_$n.pptx
  python3 add_num.py $n b3_$n.pptx final_$n.pptx > /dev/null
done
