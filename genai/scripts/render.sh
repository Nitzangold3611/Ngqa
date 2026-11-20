#!/bin/bash
# render.sh N  -> out/rN/s-XX.jpg
n=$1; cd /home/claude/genai
python3 gbuild.py $n spec/ch$n.jsonl out/g$n.pptx || exit 1
cd out && rm -rf r$n && mkdir r$n && timeout 400 python3 /root/.claude/skills/synced/*/pptx/scripts/office/soffice.py --headless --convert-to pdf --outdir r$n g$n.pptx >/dev/null 2>&1
pdftoppm -r 72 -jpeg r$n/g$n.pdf r$n/s 2>/dev/null; ls r$n | wc -l
