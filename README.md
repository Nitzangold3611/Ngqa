# NGQA · מצגות קורסים

אתרי המצגות של NGQA ייעוץ והדרכה בבדיקות תוכנה.

אתר אחד לכל הקורסים: **https://courses.ngqa.net** (זמנית: https://ngqa-ctfl40.netlify.app)

| קורס | נתיב באתר | מקור |
|---|---|---|
| ISTQB CTFL 4.0 | `/courses/ctfl/` | `site/courses/ctfl/`, `ctfl/scripts/` |
| CT-GenAI – בינה מלאכותית יוצרת בבדיקות תוכנה | `/courses/genai/` | `site/courses/genai/`, `genai/scripts/`, `genai/spec/` |

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
