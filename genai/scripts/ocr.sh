#!/bin/bash
f=$1; b=$(basename $(dirname $f))_$(basename $f .jpg)
tesseract "$f" ocr/$b -l heb+eng --psm 3 >/dev/null 2>&1
