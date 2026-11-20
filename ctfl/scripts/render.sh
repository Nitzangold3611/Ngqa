#!/bin/bash
# render.sh deck.pptx outdir [dpi]
S=/root/.claude/skills/synced/d581b97c-8232-4796-9289-5c7868eb7101_0c95616f-1c1c-47af-8e20-d3b0c58604f4/pptx/scripts
rm -rf $2; mkdir -p $2; cp $1 $2/deck.pptx
(cd $2 && timeout 600 python3 $S/office/soffice.py --headless --convert-to pdf deck.pptx >/dev/null 2>&1)
pdftoppm -r ${3:-60} -jpeg $2/deck.pdf $2/s 2>/dev/null
ls $2 | wc -l
