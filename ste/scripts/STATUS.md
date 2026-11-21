# CT-STE course build — status
Source: /Volumes/NGQA/קורסים NGQA/ct-ste/מצגות (slides are images). Extracted to /home/claude/ste/src/{c1..c9,exam,proj}_NNN.jpg
Workflow: python3 grid.py cN a b -> read /tmp/g_cN_a.jpg -> append specs to spec/chN.jsonl (gbuild layouts) -> ./run.sh N -> QA out/gN_*.jpg
Builder: mkbuild.py (from /home/claude/sql/mkbuild.py) -> stbuild.py; chapters.json names.
Spec gotchas: cover use obj (no x); lead = {h,x}; dia tip needs lab; rows = [label,sub,value]; steps groups = ranges (avoid); vslab short ('VS').
Decisions (user): full redesign in NGQA style; sample exam as slides (question slide + answer slide); project deck + guidelines doc + shoponline spec doc.
Done: ch1, ch2 (cover: obj only, no x/date/cert)
- ch3 done (56 slides) 20:32
- ch4 done (46)
- ch5 done (50)
- ch6 done (47)
- ch7 done (43)
- ch8 done (52)
- exam ch10 done (83)
