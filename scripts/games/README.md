# NGQA games toolkit

Learning games for every course. All pages live under `site/courses/<id>/` and are protected by the course role (see `_redirects`).

| Script | What it builds | Source per course |
|---|---|---|
| `escape.py <id> <LABEL> <content.py>` | `escape/index.html` (answers stored as salted SHA-256) + `pdf/NGQA-<LABEL>-escape-solutions.pdf` | `<course>/games/escape.py` (genai: `genai/escape/content.py`) |
| `puzzles.py <id> <LABEL> <words.py>` | `puzzles/index.html` — crossword (תשבץ) + cryptic crossword (תשחץ) | `<course>/games/words.py` (genai: `genai/puzzles/words.py`) |
| `quiz.py <id> <LABEL> <questions.py>` | `quiz/index.html` — chapter review MCQs with per-option explanations | `genai/quiz/questions.py` |
| `add_aux.py [ids…]` | the "חומרי עזר" box on each course page (idempotent) | — |

`build_course.py` strips the box from the genai template and re-adds it per course.
Escape-room content files: each lock has `ans`, three graded `hints` and `why` (used in the solutions PDF); room rewards must spell `FINAL` (checked by the builder).
SQL escape room data: `sql/games/escape_setup.sql` (copied to `site/courses/sql/dl/`).
