# -*- coding: utf-8 -*-
TITLE = 'חדר בריחה: היהלום שנעלם'
FINAL = 'SELECT'
CERT_TITLE = 'התעלומה נפתרה! 🎉'
CERT = 'בעזרת SELECT, ‏WHERE, פונקציות, JOIN ושאילתות משנה מצאתם את הגנב — כמו בודק שמאמת נתונים ישירות במסד.'
INTRO = '''<p>בוקר שבת, 21.11.2026. יהלום "Blue Star" נעלם מאולם האבנים היקרות במוזיאון. המשטרה עוד בדרך, ומנהלת המוזיאון סגרה את כל הדלתות. המפתח היחיד לחדר הבקרה נמצא אצלכם: גישה למסד הנתונים של המוזיאון.</p>
<p><b>לפני שמתחילים:</b> הורידו את <a href="../dl/escape_setup.sql" download>escape_setup.sql</a>, פתחו אותו ב-SSMS בתוך מסד נתונים ריק לתרגול, והריצו אותו. נוצרות ארבע טבלאות: <code>Halls</code>, ‏<code>Exhibits</code>, ‏<code>Staff</code> ו-<code>AccessLog</code>. כל התשובות מגיעות מהרצת שאילתות. אפשר גם לפתור על הנייר, אבל זה הרבה יותר קשה.</p>
<p>יש לכם <b>75 דקות</b>. בכל מנעול יש 3 רמזים, וכל רמז מוסיף 3 דקות. כל חדר שתפרצו יחשוף אות ואת מיקומה בסיסמה הסופית.</p>'''

ROOMS = [
 dict(id='r1', n=1, title='חדר כוח האדם', sub='פרקים 1–2 · SELECT, ‏WHERE ו-ORDER BY', reward=('E', 2),
  body='''<p>הבלש מבקש להתחיל מרשימת העובדים. כל העובדים נמצאים בטבלה <code>Staff</code>.</p>''',
  locks=[
   dict(id='r1a', label='כמה עובדים יש במחלקת האבטחה (Security)?', fmt='מספר', ans='4',
        hints=['השתמשו ב-COUNT(*) עם תנאי WHERE.', "התנאי הוא Department = 'Security'.", "SELECT COUNT(*) FROM Staff WHERE Department = 'Security';"],
        why="SELECT COUNT(*) FROM Staff WHERE Department = 'Security'; — מחזירה 4 (Cohen, ‏Levi, ‏Ben-David, ‏Peretz)."),
   dict(id='r1b', label='מה שם המשפחה של העובד שהתקבל לעבודה אחרון?', fmt='שם משפחה באנגלית', ans='PERETZ',
        hints=['צריך למיין לפי HireDate.', 'מיון יורד (DESC) והצגת השורה הראשונה בלבד.', 'SELECT TOP 1 LastName FROM Staff ORDER BY HireDate DESC;'],
        why='SELECT TOP 1 LastName FROM Staff ORDER BY HireDate DESC; — מחזירה Peretz, שהתקבל ב-5.1.2025.'),
  ]),
 dict(id='r2', n=2, title='חדר המוצגים', sub='פרק 3 · BETWEEN, ‏IN ו-LIKE', reward=('L', 3),
  body='''<p>חברת הביטוח רוצה לדעת אילו מוצגים "בטווח הסיכון" שלה, ומה עוד עלול להיעלם.</p>''',
  locks=[
   dict(id='r2a', label='כמה מוצגים שווים בין 400,000 ל-1,000,000 (כולל), והסטטוס שלהם הוא OnDisplay או Restoration?', fmt='מספר', ans='4',
        hints=['השתמשו ב-BETWEEN לערך וב-IN לסטטוס.', 'BETWEEN כולל את שני הקצוות.', "SELECT COUNT(*) FROM Exhibits WHERE InsuranceValue BETWEEN 400000 AND 1000000 AND Status IN ('OnDisplay','Restoration');"],
        why='המוצגים: Night Harbor ‏(650,000), ‏Golden Owl ‏(920,000), ‏Emerald Ring ‏(760,000, ‏Restoration) ו-Sunset Field ‏(410,000). ‏Ruby Crown יקר מדי ו-Marble Runner זול מדי. סה"כ 4.'),
   dict(id='r2b', label='בכמה שמות משפחה של עובדים מופיעה האות a (בכל מקום בשם)?', fmt='מספר', ans='5',
        hints=["השתמשו ב-LIKE עם התו הכללי %.", "LastName LIKE '%a%' — ברירת המחדל ב-SQL Server לא מבחינה בין אותיות גדולות לקטנות.", "SELECT COUNT(*) FROM Staff WHERE LastName LIKE '%a%';"],
        why="SELECT COUNT(*) FROM Staff WHERE LastName LIKE '%a%'; — ‏Azulai, ‏Ben-David, ‏Shapiro, ‏Golan, ‏Katz. סה\"כ 5."),
  ]),
 dict(id='r3', n=3, title='חדר הכספים', sub='פרקים 4–5 · פונקציות מוכללות, GROUP BY ושאילתות משולבות', reward=('T', 6),
  body='''<p>המשטרה בודקת מניעים כלכליים. ההנהלה מבקשת תמונת מצב כספית.</p>''',
  locks=[
   dict(id='r3a', label='לאיזו מחלקה יש את השכר הממוצע הגבוה ביותר?', fmt='שם המחלקה באנגלית', ans='IT',
        hints=['השתמשו ב-AVG עם GROUP BY Department.', 'מיינו לפי הממוצע בסדר יורד.', 'SELECT Department, AVG(Salary) AS AvgSalary FROM Staff GROUP BY Department ORDER BY AvgSalary DESC;'],
        why='הממוצעים: IT ‏16,500 · ‏Curatorial ‏14,650 · ‏Security ‏10,450 · ‏Maintenance ‏9,000. התשובה: IT.'),
   dict(id='r3b', label='מה שווי הביטוח הכולל של המוצגים שנשארו באולם Gems (בלי המוצג שנעלם)?', fmt='מספר, בלי פסיקים', ans='3480000',
        hints=['צריך את HallID של האולם Gems — מהטבלה Halls.', "SUM(InsuranceValue) עם תנאי על האולם ועל Status <> 'Missing'.", "SELECT SUM(InsuranceValue) FROM Exhibits WHERE HallID = 'H2' AND Status <> 'Missing';"],
        why='באולם H2 ‏(Gems) נשארו Ruby Crown ‏(1,800,000), ‏Golden Owl ‏(920,000) ו-Emerald Ring ‏(760,000). הסכום: 3,480,000.'),
  ]),
 dict(id='r4', n=4, title='חדר יומן הכניסות', sub='פרק 6 · JOIN', reward=('S', 1),
  body='''<p>המצלמה באולם Gems הייתה מושבתת בין <b>22:00 ל-23:30</b> ב-20.11.2026. כל כניסה דרך הדלת <code>D-GEMS</code> נרשמה בטבלה <code>AccessLog</code>, אבל שם יש רק מספרי עובדים — את השמות צריך להביא מ-<code>Staff</code>.</p>''',
  locks=[
   dict(id='r4a', label='כמה עובדים שונים נכנסו בדלת D-GEMS בחלון הזמן 22:00–23:30 (לפי שעת הכניסה)?', fmt='מספר', ans='3',
        hints=['התחילו מ-AccessLog וסננו לפי Door ולפי EntryTime.', "EntryTime BETWEEN '2026-11-20T22:00:00' AND '2026-11-20T23:30:00'.", 'COUNT(DISTINCT StaffID) — ואם רוצים שמות, JOIN ל-Staff.'],
        why="SELECT s.FirstName, s.LastName FROM AccessLog a JOIN Staff s ON s.StaffID = a.StaffID WHERE a.Door = 'D-GEMS' AND a.EntryTime BETWEEN '2026-11-20T22:00:00' AND '2026-11-20T23:30:00'; — שלושה חשודים: Yael Golan ‏(22:10), ‏Ron Azulai ‏(22:50) ו-Noa Shapiro ‏(23:10). ‏Avi Levi נכנס לפני החלון, ו-Lior Ben-David אחריו."),
   dict(id='r4b', label='מה סכום המשכורות של שלושת החשודים?', fmt='מספר, בלי פסיקים', ans='30800',
        hints=['אותו JOIN ואותו תנאי — רק עם SUM.', 'SUM(s.Salary).', '7,600 + 10,400 + 12,800.'],
        why='SUM(s.Salary) על אותו JOIN: ‏7,600 + 10,400 + 12,800 = 30,800.'),
  ]),
 dict(id='r5', n=5, title='חדר החקירה', sub='פרק 7 · שאילתות משנה', reward=('C', 5),
  body='''<p>מנהלת המוזיאון נזכרת: <q>הכספת עם המפתח הרזרבי של תיבת היהלום נמצאת בארכיון. מי שגנב חייב היה לעבור קודם בארכיון — באותו ערב.</q> הדלת של הארכיון היא <code>D-ARCH</code>.</p>''',
  locks=[
   dict(id='r5a', label='מה שם המשפחה של העובד שנכנס ל-D-GEMS בחלון הזמן, וגם נכנס ל-D-ARCH ב-20.11.2026?', fmt='שם משפחה באנגלית', ans='SHAPIRO',
        hints=['שתי שאילתות משנה עם IN — אחת לכל דלת.', "התנאי השני: Door = 'D-ARCH' AND EntryTime >= '2026-11-20T00:00:00' AND EntryTime < '2026-11-21T00:00:00'.", 'SELECT LastName FROM Staff WHERE StaffID IN (…D-GEMS בחלון…) AND StaffID IN (…D-ARCH באותו יום…);'],
        why="SELECT LastName FROM Staff WHERE StaffID IN (SELECT StaffID FROM AccessLog WHERE Door = 'D-GEMS' AND EntryTime BETWEEN '2026-11-20T22:00:00' AND '2026-11-20T23:30:00') AND StaffID IN (SELECT StaffID FROM AccessLog WHERE Door = 'D-ARCH' AND EntryTime >= '2026-11-20T00:00:00' AND EntryTime < '2026-11-21T00:00:00'); — מחזירה Shapiro. ‏Klein נכנסה לארכיון יום קודם, ולכן לא עונה על התנאי."),
  ]),
 dict(id='r6', n=6, title='חדר השינויים', sub='פרקים 8–11 · DML, ‏DDL, ‏Views ופרוצדורות', reward=('E', 4),
  body='''<p>לפני שהמשטרה מגיעה, מישהו מנסה "לנקות" את המסד. מצאתם שתי פקודות שמוכנות להרצה:</p>
<div class="cfg"><pre dir="ltr">-- (1)
UPDATE Staff
SET Salary = Salary * 1.05
WHERE Department IN (SELECT Department FROM Staff
                     GROUP BY Department
                     HAVING COUNT(*) &gt;= 3);

-- (2)
DELETE FROM AccessLog
WHERE ExitTime &lt; '2026-11-20T00:00:00';</pre></div>
<p>עדיף לבדוק בתוך <code>BEGIN TRANSACTION; … ROLLBACK;</code> כדי לא לאבד ראיות.</p>''',
  locks=[
   dict(id='r6a', label='כמה שורות תעדכן פקודה (1)? ואחרי פקודה (2), כמה שורות יישארו ב-AccessLog? (על הנתונים המקוריים)', fmt='שני המספרים ברצף, לדוגמה: 512', ans='411',
        hints=['בפקודה (1): אילו מחלקות מופיעות 3 פעמים או יותר?', 'רק למחלקת Security יש 4 עובדים. בפקודה (2): כמה כניסות יצאו לפני 20.11?', 'פקודה (1) מעדכנת 4 שורות; פקודה (2) מוחקת שורה אחת מתוך 12.'],
        why='(1): שאילתת המשנה מחזירה רק את Security ‏(4 עובדים), ולכן מתעדכנות 4 שורות. (2): רק כניסה 9 (Klein, ‏19.11) יצאה לפני 20.11, ולכן נמחקת שורה אחת ונשארות 11. התשובה: 4 ואז 11 — ‏411.'),
  ]),
]

FINAL_LOCK = dict(id='fin', label='הרכיבו את הסיסמה הסופית מששת האותיות, כל אחת במיקום שלה.', fmt='6 אותיות', ans=FINAL,
  hints=['כל חדר חשף אות ומספר. המספר הוא המיקום בסיסמה.', 'זו מילת המפתח הראשונה שלמדתם ב-SQL.', 'S E L E C T'],
  why='S(1) E(2) L(3) E(4) C(5) T(6) — SELECT. והגנבת: Noa Shapiro.')
