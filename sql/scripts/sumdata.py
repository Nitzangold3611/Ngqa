import json, re
C = [
 ("מצא את שמו הפרטי ומספר הסטודנט של מר בראון (Brown).", "SELECT First, ID\nFROM Student\nWHERE Last = 'Brown';", ''),
 ("סדר מחדש את טבלת הסטודנטים בסדר יורד לפי מספר הסטודנט ובסדר עולה לפי שם המשפחה. דאג שהעמודות First ו-Last יוצגו בשמות First Name ו-Last Name.", "SELECT ID, First AS [First Name], Last AS [Last Name]\nFROM Student\nORDER BY ID DESC, Last ASC;", ''),
 ("עדכן לתלמידה S104 שם משפחה חדש בעקבות נישואיה: Jones-Abutbul.", "UPDATE Student\nSET Last = 'Jones-Abutbul'\nWHERE ID = 'S104';", 'שימו לב: העמודה Last מוגדרת char(10) והשם החדש ארוך יותר, ולכן תתקבל שגיאת קיצור (String or binary data would be truncated). אפשר להגדיל קודם את העמודה: ALTER TABLE Student ALTER COLUMN Last varchar(20);'),
 ("מצא את ממוצע הציונים שהתקבלו בקורס תכנות 2.", "SELECT AVG(G.Grade) AS AvgGrade\nFROM Grade AS G\nINNER JOIN Course AS C ON G.Code = C.Code\nWHERE C.Title = 'Programming 2';", 'תוקן: AVEG → AVG'),
 ("הכנס תלמיד חדש למערכת: S108, תומר (לא מסר שם משפחה בשלב זה).", "INSERT INTO Student (ID, First, Last)\nVALUES ('S108', 'Tomer', NULL);", ''),
 ("מחק לתלמיד S104 את הציון בלבד מהרשימה הרלוונטית.", "UPDATE Grade\nSET Grade = NULL\nWHERE ID = 'S104';", ''),
 ("מצא מהו הציון הגבוה ביותר שהתקבל בקורס ניהול פרויקטים.", "SELECT MAX(G.Grade) AS MaxGrade\nFROM Grade AS G\nINNER JOIN Course AS C ON G.Code = C.Code\nWHERE C.Title = 'Project Mgmt';", ''),
 ("מצא את הציונים שקיבלו כל הסטודנטים ששמם הפרטי הוא John.", "SELECT G.Grade\nFROM Grade AS G\nINNER JOIN Student AS S ON G.ID = S.ID\nWHERE S.First = 'John';", ''),
 ("מצא את סכום כל הציונים שהתקבלו יחד מהתלמידים S103 עד S107 (ללא התלמיד S104).", "SELECT SUM(Grade) AS TotalGrades\nFROM Grade\nWHERE ID BETWEEN 'S103' AND 'S107' AND ID <> 'S104';\n\n-- או:\n-- WHERE ID IN ('S103', 'S105', 'S106', 'S107');", 'תוקן: בקובץ המקורי הופיעו שתי הוראות WHERE ברצף; השנייה הועברה להערה כחלופה'),
 ("מצא את שמות המשפחה של כל הסטודנטים, ועבור אלו שנבחנו הצג לצד השם את קוד הקורס שבו נבחנו.", "SELECT S.Last, G.Code\nFROM Student AS S\nLEFT JOIN Grade AS G ON G.ID = S.ID;", ''),
 ("מצא את שם הקורס שיש בו נכשלים (נכשל = ציון נמוך מ-60).", "SELECT DISTINCT C.Title\nFROM Course AS C\nINNER JOIN Grade AS G ON G.Code = C.Code\nWHERE G.Grade < 60;", 'נוסף DISTINCT כדי שכל קורס יופיע פעם אחת'),
 ("מצא את ממוצע הציונים של התלמיד John Good.", "SELECT AVG(G.Grade) AS AvgGrade\nFROM Grade AS G\nINNER JOIN Student AS S ON G.ID = S.ID\nWHERE S.First = 'John' AND S.Last = 'Good';", ''),
]
H = [
 ("מצא את 3 המשכורות הגבוהות ביותר מתוך עמודת משכורות המינימום, כנה את העמודה MIN_MAX_SALARY, וסדר בסדר יורד (בלי נהגים ומורים).", "SELECT TOP 3 min_salary AS MIN_MAX_SALARY\nFROM JOBS\nWHERE job_title NOT IN ('Drivers', 'Teachers')\nORDER BY min_salary DESC, job_id DESC;", 'תוקן ל-T-SQL: LIMIT 3 → TOP 3'),
 ("שלוף את שם העובד, שם משפחתו וכותרת התפקיד שלו.", "SELECT E.first_name, E.last_name, J.job_title\nFROM EMPLOYEES AS E\nINNER JOIN JOBS AS J ON E.job_id = J.job_id;", ''),
 ("עדכן בטבלת המיקומים לכולם עיר = ערך ריק, למעט המיקומים בקוד מדינה 972.", "UPDATE LOCATIONS\nSET city = NULL\nWHERE country_id <> '972';", ''),
 ("הצג את מספרי המנהלים של העובדים בחברה, ועבור אלו שרשומה להם מחלקה הוסף גם את מספר המחלקה.", "SELECT manager_id, department_id\nFROM EMPLOYEES;", 'תוקן שם העמודה managr_id → manager_id'),
 ("מצא את כל פרטי המדינות שמופיעות גם בטבלת המיקומים.", "SELECT *\nFROM COUNTRIES\nWHERE country_id IN (SELECT country_id FROM LOCATIONS);", 'תוקן: שמות טבלה ועמודה שגויים, והצירוף המקורי החזיר כל מדינה כמה פעמים'),
 ("מצא את מספר התפקיד ומספר המחלקה של כל העובדים שהתחילו לעבוד בשנת 2009.", "SELECT job_id, department_id\nFROM EMPLOYEES\nWHERE YEAR(hire_date) = 2009;", "הוחלף LIKE '%2009%' ב-YEAR(), שעובד נכון על עמודת תאריך"),
 ("הצג את כל מספרי האזורים, ועבור אזורים שמחוברים למדינות הצג גם את שמות המדינות. סדר לפי שם המדינה בסדר יורד.", "SELECT R.region_id, C.country_name\nFROM REGIONS AS R\nLEFT JOIN COUNTRIES AS C ON R.region_id = C.region_id\nORDER BY C.country_name DESC;", 'תוקנו שמות הטבלאות'),
 ("הצג את ממוצע המשכורות של העובדים בעמודה אחת.", "SELECT AVG(salary) AS AvgSalary\nFROM EMPLOYEES;", ''),
 ("מצא כמה רשומות קיימות בטבלת המדינות.", "SELECT COUNT(*) AS CountriesCount\nFROM COUNTRIES;", ''),
 ("מצא את הערך המינימלי של עמודת המשכורת המקסימלית בטבלת התפקידים.", "SELECT MIN(max_salary)\nFROM JOBS;", ''),
 ("מצא את שמות המשפחה של 5 העובדים שמשתכרים הכי גבוה בחברה.", "SELECT TOP 5 last_name\nFROM EMPLOYEES\nORDER BY salary DESC;", 'תוקן ל-T-SQL: LIMIT 5 → TOP 5'),
 ("מצא את סכום כל המשכורות שהחברה משלמת לעובדים וכנה את העמודה TOTAL.", "SELECT SUM(salary) AS TOTAL\nFROM EMPLOYEES;", ''),
 ("מצא את תאריך סיום העבודה ומספר המחלקה של כל העובדים שמסיימים לעבוד השנה.", "SELECT end_date, department_id\nFROM JOB_HISTORY\nWHERE YEAR(end_date) = YEAR(GETDATE());", "השנה הקבועה 2021 הוחלפה בשנה הנוכחית"),
 ("מצא את שם המחלקה וקוד המדינה עבור מחלקות שממוקמות בעיר ברצלונה.", "SELECT D.department_name, L.country_id\nFROM DEPARTMENTS AS D\nINNER JOIN LOCATIONS AS L ON D.location_id = L.location_id\nWHERE L.city = 'Barcelona';", 'תוקן שם העמודה locatin_id'),
 ("מצא את מספר העובד, העמלה שהוא מקבל, ומספר ושם המחלקה שהוא מנהל, רק עבור מנהלים בפועל.", "SELECT E.employee_id, E.commission_pct, D.department_id, D.department_name\nFROM DEPARTMENTS AS D\nINNER JOIN EMPLOYEES AS E ON D.manager_id = E.employee_id;", 'הוחלף הפתרון: מנהל בפועל הוא העובד שמופיע ב-DEPARTMENTS.manager_id'),
]
PQ = ["שלוף את שמותיהם בלבד של מי שאישר הגעה למסיבה (כלומר כל מי שמופיע בטבלה).", "שלוף את שמם וגילם של כל מי שעדכן באיזה אמצעי תחבורה יגיע.", "אתר את כל פרטי האנשים שמגיעים מנתניה.", "אתר את פרטי כל מי שמגיע במונית או ברכבת.", "אתר את פרטי כל הגברים במסיבה.", "אתר את כל פרטי שלושת המבוגרים ביותר במסיבה.", "אתר את כל פרטי מי שמגיע למסיבה ואינו ממחלקת מכירות.", "אתר את גילו ושמו של מי שלא מסר אם הוא מעוניין בארוחה בשרית או חלבית.", "אתר שם, גיל ומין של מי שלא ידוע איך הוא מתכונן להגיע למסיבה.", "אתר את מחלקתו של מי שמעוניין לשתות יין או וודקה, או שלא מסר שום הודעה בעניין השתייה.", "אתר את שמו, ארוחתו, מחלקתו וגילו של מי ששותה בירה.", "אתר את שמו וגילו של כל מי ששותה וודקה, מים או פפסי.", "אתר את מינו של מי ששותה בירה ופפסי יחד.", "אתר את שמו ועיר מגוריו של כל מי שדיווח מה הוא רוצה לשתות.", "מיין את הטבלה בסדר עולה לפי גיל המשתתפים.", "הצג את שם המשתתפים והמשקאות שהזמינו, עבור כל מי שמגיע מעיר ששמה מכיל את האות A.", "שלוף את כל מי ששמו מסתיים באות I באנגלית.", "הצג את גילו של כל מי שמגיע ממחלקת מכירות והזמין ארוחה בשרית.", "שלוף את המשקאות של כל מי שאינו ממחלקת הנהלה.", "שלוף את שם המשתתף ומחלקתו של כל מי שמעל גיל 30.", "שלוף את שמו של כל מי שמתחת לגיל 60 ומגיע ברכב או ברכבת.", "ערוך את הטבלה בסדר חדש לפי שם העיר בסדר עולה.", "הצג את המשקה שהזמין מי שלא דיווח איך יגיע וגם לא דיווח מה ירצה לאכול.", "שלוף את אמצעי התחבורה והגיל של כל מי שלא דיווח על הארוחה הרצויה.", "שלוף את המזון, המשקה, השם והגיל של כל מי שאינו ממחלקת הנהלה או מכירות.", "שלוף את סוג המשקה והארוחה של כל מי ששמו דודי או מירב.", "שלוף את שמות הנשים שגילן בין 20 ל-40.", "שלוף את שם מי שמעל גיל 18, שייך למחלקת מכירות ומעוניין לשתות מים במסיבה.", "שלוף את שמות כל הנשים שמגיעות בכל אמצעי למעט אופניים.", "שלוף את המשקאות, הארוחה והשם של כל מי שאינו מגיע מרמלה, גדרה או חולון.", "שלוף את שם העיר של מי שמעל גיל 40, אינו ממחלקת ההנהלה ושמו מתחיל באות D."]
raw = open('/mnt/user-data/uploads/sql/תרגילים מסכמים/party/פתרונות').read()
parts = re.split(r'(?m)^(\d+)\s*$', raw)[1:]
PS = {int(a): b.strip() for a, b in zip(parts[0::2], parts[1::2])}
KW = r'\b(select|from|where|order by|top|in|is not null|is null|not in|and|or|like|between|desc|asc|null)\b'


def pretty(s):
    s = re.sub(KW, lambda m: m.group(1).upper(), s, flags=re.I)
    return '\n'.join(l.rstrip().replace('  ', ' ') for l in s.splitlines())


PF = {
 6: ("SELECT TOP 3 *\nFROM Party\nORDER BY Age DESC;", 'השאלה מבקשת את כל הפרטים, לכן * במקום age בלבד'),
 10: ("SELECT Department\nFROM Party\nWHERE Drink1 IN ('Wine', 'Vodka') OR Drink2 IN ('Wine', 'Vodka')\n   OR (Drink1 IS NULL AND (Drink2 IS NULL OR Drink2 = ''));", 'לא מסר הודעה על שתייה = שני המשקאות ריקים (NULL או מחרוזת ריקה)'),
 25: ("SELECT Name, Food, Drink1, Drink2, Age\nFROM Party\nWHERE Department NOT IN ('management', 'sales');", 'נוספה העמודה Name שהשאלה מבקשת'),
 28: ("SELECT Name\nFROM Party\nWHERE Age > 18 AND Department = 'sales'\n  AND (Drink1 = 'water' OR Drink2 = 'water');", 'נוספו סוגריים: בלעדיהם ה-OR עוקף את שאר התנאים'),
 29: ("SELECT Name\nFROM Party\nWHERE Gender = 'F' AND (Transport <> 'bike' OR Transport IS NULL);", 'NOT IN לא מחזיר שורות שבהן Transport הוא NULL; אם רוצים לכלול גם את מי שלא דיווח, מוסיפים IS NULL'),
 30: ("SELECT Drink1, Drink2, Food, Name\nFROM Party\nWHERE City NOT IN ('Ramla', 'Gadera', 'Holon');", "תוקן שם העיר: בטבלה היא כתובה Ramla ולא ramle"),
}
P = []
for k, q in enumerate(PQ, 1):
    a, note = PF.get(k, (pretty(PS[k]), ''))
    P.append((q, a, note))
SUM = [
 {'id': 'college', 'title': 'College', 'sub': 'סטודנטים, קורסים וציונים', 'credit': '',
  'about': 'שלוש טבלאות: Student (ID, First, Last), Course (Code, Title) ו-Grade (ID, Code, Grade). מריצים את קובץ ההקמה במסד נתונים חדש ופותרים.',
  'setup': 'college_setup.sql', 'tables': ['Student', 'Course', 'Grade'], 'items': C},
 {'id': 'party', 'title': 'Party', 'sub': 'מסיבת החברה · טבלה אחת', 'credit': '',
  'about': 'טבלה אחת, Party, עם רשימת המוזמנים: עיר, מחלקה, גיל, מין, אמצעי הגעה, ארוחה ושני משקאות. שימו לב לערכים חסרים (NULL ומחרוזת ריקה).',
  'setup': 'party_setup.sql', 'tables': ['Party'], 'items': P},
]
for s in SUM:
    s['items'] = [{'q': q, 'a': a, 'fixed': n} for q, a, n in s['items']]
json.dump(SUM, open('/home/claude/sql/sum/summary.json', 'w'), ensure_ascii=False, indent=1)
print([(s['id'], len(s['items']), sum(1 for i in s['items'] if i['fixed'])) for s in SUM])

# ---- new summary exercises (SQL_Practice_HE): veterinary clinic, museum, space missions
import html as _h
SRC = '/mnt/user-data/uploads/SQL_Practice_HE'
NEW = [('01_veterinary', 'vet', 'מרפאה וטרינרית', 'בעלי חיים, טיפולים וביקורים', '🐾'),
       ('02_museum', 'museum', 'מוזיאון ותערוכות', 'אמנים, יצירות ואולמות תצוגה', '🖼️'),
       ('03_space', 'space', 'משימות חלל', 'חלליות, יעדים ומשימות מחקר', '🚀')]
for k, id_, title, sub, ic in NEW:
    t = open(f'{SRC}/{k}_exercise.html').read()
    qs = [_h.unescape(re.sub('<[^>]+>', '', q)).strip() for q in re.findall(r'<div class="question"><span class="num">\d+</span>(.*?)<div class="blank">', t, re.S)]
    a = open(f'{SRC}/{k}_answers.sql').read()
    parts = re.split(r'(?m)^-- Question (\d+)\s*$', a)[1:]
    ans = {int(n): b.strip().replace('-- Verify:', '-- בדיקה:') for n, b in zip(parts[0::2], parts[1::2])}
    setup = open(f'{SRC}/{k}_setup.sql').read()
    tabs = [f"{n} ({', '.join(c.strip().split()[0] for c in body.split(',\n') if c.strip() and not c.strip().upper().startswith(('PRIMARY', 'FOREIGN')))})"
            for n, body in re.findall(r'CREATE TABLE (\w+)\s*\((.*?)\n\);', setup, re.S)]
    open(f'/home/claude/sql/sum/dl/{id_}_setup.sql', 'w').write(setup)
    items = [{'q': q, 'a': ans[i], 'fixed': ''} for i, q in enumerate(qs, 1)]
    SUM.append({'id': id_, 'title': title, 'sub': sub, 'credit': '', 'ic': ic,
                'about': 'מקימים את הטבלאות מקובץ ההקמה במסד תרגול ריק, ופותרים. כל שאלה מתייחסת לנתוני הפתיחה: את שאלות ה-INSERT וה-UPDATE מריצים בתוך BEGIN TRANSACTION … ROLLBACK.',
                'setup': f'{id_}_setup.sql', 'tables': tabs, 'items': items})
for s in SUM:
    s.setdefault('ic', {'college': '🎓', 'party': '🎉'}.get(s['id'], '📋'))
json.dump(SUM, open('/home/claude/sql/sum/summary.json', 'w'), ensure_ascii=False, indent=1)
print([(s['id'], len(s['items']), s['tables'][:1]) for s in SUM])
