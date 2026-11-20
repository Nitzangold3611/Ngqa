import re
KW = [
    ('bug', ['פגם', 'פגמים', 'באג', 'תקל', 'כשל', 'defect', 'bug', 'failure', 'incident', 'שגיא']),
    ('risk', ['סיכון', 'סיכונים', 'risk']),
    ('security', ['אבטח', 'security', 'הרשא', 'חדיר']),
    ('perf', ['ביצועים', 'עומס', 'performance', 'load', 'stress', 'מהירות']),
    ('devops', ['devops', 'ci/cd', 'continuous', 'אינטגרציה רציפה', 'jenkins', 'pipeline', 'shift left', 'shift-left']),
    ('agile', ['אג\'ייל', 'אג׳ייל', 'agile', 'scrum', 'סקראם', 'ספרינט', 'sprint', 'kanban', 'קנבן', 'retrospective', 'רטרוספקטיב']),
    ('estimate', ['הערכ', 'estimation', 'אומדן', 'planning poker', 'מאמץ']),
    ('metrics', ['מדד', 'מדדים', 'metric', 'דוח', 'דו"ח', 'report', 'ניטור', 'monitor', 'בקרה', 'control']),
    ('cost', ['עלות', 'עלויות', 'cost', 'כסף', 'תקציב', 'roi']),
    ('config', ['תצורה', 'configuration', 'גרס', 'version', 'baseline']),
    ('tools', ['כלי', 'כלים', 'tool', 'אוטומצי', 'automation', 'framework']),
    ('review', ['סקיר', 'review', 'סטטי', 'static', 'inspection', 'walkthrough', 'קריאה']),
    ('design', ['טכניק', 'technique', 'מחלקות שקילות', 'equivalence', 'boundary', 'גבול', 'טבלת החלטות', 'decision', 'state', 'מצבים', 'עיצוב בדיקות', 'test design']),
    ('code', ['קוד', 'code', 'white box', 'קופסה לבנה', 'statement', 'branch', 'פיתוח', 'developer', 'מפתח']),
    ('docs', ['דריש', 'requirement', 'מסמך', 'document', 'תיעוד', 'user story', 'סיפור משתמש', 'specification', 'אפיון']),
    ('plan', ['תכנון', 'תוכנית', 'plan', 'לוח זמנים', 'schedule', 'שלבי']),
    ('users', ['לקוח', 'משתמש', 'קבלה', 'acceptance', 'customer', 'user', 'uat', 'stakeholder', 'בעלי עניין']),
    ('team', ['צוות', 'team', 'תקשורת', 'communication', 'שיתוף', 'collaborat', 'whole team']),
    ('roles', ['תפקיד', 'role', 'עצמאות', 'independ', 'מנהל', 'manager', 'בודק']),
    ('levels', ['רמות', 'level', 'יחידה', 'unit', 'מערכת', 'system', 'component', 'רכיב', 'integration', 'אינטגרציה']),
    ('process', ['תהליך', 'process', 'מחזור חיים', 'lifecycle', 'מודל', 'model', 'sdlc', 'פעילויות']),
    ('change', ['תחזוק', 'maintenance', 'שינוי', 'change', 'רגרסי', 'regression', 'confirmation']),
    ('goal', ['מטר', 'objective', 'goal', 'יעד', 'עקרונות', 'principle']),
    ('learn', ['ידע', 'מיומנו', 'skill', 'למיד', 'הכשר', 'knowledge', 'ניסיון']),
    ('data', ['נתונים', 'data', 'database', 'בסיס נתונים']),
    ('env', ['סביבת', 'environment', 'שרת', 'server', 'תשתית']),
    ('question', ['מה ', 'למה', 'מדוע', 'why', 'what', '?']),
    ('quality', ['איכות', 'quality', 'qa', 'qc', 'בדיק', 'test']),
]
ORDER = [k for k, _ in KW]


def topic_for(title, body, used, last=None):
    tl, bl = title.lower(), body.lower()
    scores = []
    for i, (k, words) in enumerate(KW):
        s = sum(tl.count(w.lower()) for w in words) * 4 + sum(min(3, bl.count(w.lower())) for w in words)
        if k == 'quality':
            s *= 0.3
        if s:
            scores.append((s - i * 0.01, k))
    scores.sort(reverse=True)
    ks = [k for _, k in scores] or ['quality']
    if ks[0] == last and len(ks) > 1:
        return ks[1]
    if ks[0] == last:
        alt = ['goal', 'learn', 'process', 'team', 'rocket', 'design', 'time']
        used['_alt'] = used.get('_alt', 0) + 1
        return alt[used['_alt'] % len(alt)]
    return ks[0]
