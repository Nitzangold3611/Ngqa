# NGQA · מצגות קורסים

אתרי המצגות של NGQA ייעוץ והדרכה בבדיקות תוכנה.

אתר אחד לכל הקורסים: **https://courses.ngqa.net** (הכתובות הישנות מפנות אליו)

| קורס | נתיב באתר | מקור |
|---|---|---|
| ISTQB CTFL 4.0 | `/courses/ctfl/` | `site/courses/ctfl/`, `ctfl/scripts/` |
| CT-GenAI – בינה מלאכותית יוצרת בבדיקות תוכנה | `/courses/genai/` | `site/courses/genai/`, `genai/scripts/`, `genai/spec/` |

## גרסאות
כל גרסה מתועדת כאן בקצרה, ובפירוט ב-[CHANGELOG.md](CHANGELOG.md). הקומיט של כל גרסה נקרא `Release vX.Y.Z`.

| גרסה | תאריך | מה כוללת |
|---|---|---|
| v3.0.1 | 20.11.2026 | מובייל, מסך מלא: החלקה באצבע עוברת בין השקפים. CTFL v3.0.1, CT-GenAI v1.1.1 |
| v3.0 | 20.11.2026 | אתר קורסים מאוחד: עמוד ראשי עם מלבן לכל קורס, `/courses/ctfl/` ו-`/courses/genai/`, דומיין courses.ngqa.net, הפניות מהכתובות הישנות, PWA אחד "NGQA הדרכות". CTFL v3.0, CT-GenAI v1.1 |
| v2.9 | 19.11.2026 | ייבוא ראשוני ל-GitHub: אתר CTFL 4.0 (v2.9) ואתר CT-GenAI (v1.0) כאתרים נפרדים, סקריפטי בנייה ותמלול שקפים |


## מבנה
- `site/` – האתר שמתפרסם (עמוד ראשי + `courses/<קורס>/`).
- `*/scripts/` – סקריפטי בנייה (יצירת המצגות וחיתוך השקפים לאתר).
- `genai/spec/` – תמלול השקפים (JSONL לכל פרק), המקור לבניית מצגות CT-GenAI.
- `genai/icons/` – אייקונים למצגות.
- `genai/redirect/` – האתר הישן ngqa-genai, מפנה לאתר המאוחד.
- `CHANGELOG.md` – יומן שינויים.

קבצי ה-PPTX המקוריים והמעוצבים נשמרים בכונן NGQA ולא בריפוזיטורי.

## פריסה
כל push ל-`main` מתפרסם אוטומטית ב-Netlify:
- ngqa-ctfl40 (האתר המאוחד, courses.ngqa.net) → Base directory: `site`
- ngqa-genai (הפניה בלבד) → Base directory: `genai/redirect`

© כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה
