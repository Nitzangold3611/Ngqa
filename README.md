# NGQA · מצגות קורסים

אתרי המצגות של NGQA ייעוץ והדרכה בבדיקות תוכנה.

| קורס | תיקייה | אתר |
|---|---|---|
| ISTQB CTFL 4.0 | `ctfl/` | https://ngqa-ctfl40.netlify.app |
| CT-GenAI – בינה מלאכותית יוצרת בבדיקות תוכנה | `genai/` | https://ngqa-genai.netlify.app |

## מבנה
- `*/site/` – האתר הסטטי שמועלה ל-Netlify (publish directory). כולל `CHANGELOG.md`.
- `*/scripts/` – סקריפטי בנייה (יצירת המצגות וחיתוך השקפים לאתר).
- `genai/spec/` – תמלול השקפים (JSONL לכל פרק), המקור לבניית מצגות CT-GenAI.
- `genai/icons/` – אייקונים למצגות.

קבצי ה-PPTX המקוריים והמעוצבים נשמרים בכונן NGQA ולא בריפוזיטורי.

© כל הזכויות שמורות ל-NGQA ייעוץ והדרכה בבדיקות תוכנה

## פריסה
כל push ל-`main` מתפרסם אוטומטית ב-Netlify:
- ngqa-ctfl40 → Base directory: `ctfl/site`
- ngqa-genai → Base directory: `genai/site`
