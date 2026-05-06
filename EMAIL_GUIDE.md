# מדריך מיילים לידים — מה צריך לעשות כדי שיעבוד

## המצב הנוכחי

- מסד הנתונים (`leads.db`) מכיל ~1,600 לידים
- לאף ליד אין כתובת מייל בעמודת `email` — לכן אין שליחת מייל כרגע
- ברגע שיש מייל לליד → הקמפיין ישלח מייל **אוטומטית** בנוסף לווצאפ

---

## שלב 1 — קבלת Gmail App Password

1. פתח את [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) עם `landingpageforu@gmail.com`
2. ודא שאימות דו-שלבי (2FA) פעיל (חובה)
3. בחר **Mail** + **Windows Computer** → לחץ **Generate**
4. קבל סיסמה בפורמט `xxxx xxxx xxxx xxxx`
5. פתח את הקובץ `e:/system/.env` והחלף:
   ```
   EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
   ```
   בסיסמה האמיתית שקיבלת

---

## שלב 2 — הוספת מיילים ללידים

### אפשרות א: ידנית (ליד בודד)

```python
# הרץ בטרמינל מתוך e:/system
py -c "
from core.database import get_conn
conn = get_conn()
conn.execute(\"UPDATE businesses SET email=? WHERE id=?\", ('email@example.com', 123))
conn.commit()
conn.close()
"
```

### אפשרות ב: סריקה אוטומטית (מומלץ)

הסקריפר יודע לחפש מיילים מ-Google Maps / אתרי הלידים:

```bash
cd e:/system
py -c "from scrapers.scraper import find_website_and_email; ..."
```

> כרגע אין סקריפט ייעודי לסריקת מיילים בלבד — יש להוסיף אחד (ראה שלב 5)

### אפשרות ג: ייבוא מ-CSV

אם יש לך קובץ CSV עם שדות `phone,email`:

```python
import csv
from core.database import get_conn

conn = get_conn()
with open('emails.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        conn.execute("UPDATE businesses SET email=? WHERE phone=?",
                     (row['email'], row['phone']))
conn.commit()
conn.close()
```

---

## שלב 3 — שליחת קמפיין מייל

לאחר שיש מיילים בDB ו-App Password מוגדר:

```bash
cd e:/system

# בדיקה (dry run — לא שולח):
py -c "from outreach.leads_email_campaign import run; run(dry_run=True)"

# שליחה אמיתית (100 מיילים):
py -c "from outreach.leads_email_campaign import run; run(dry_run=False, daily_limit=100)"

# שליחה לליד ספציפי לפי ID:
py -c "from outreach.leads_email_campaign import run; run(dry_run=False, only_lead_id=868)"
```

---

## שלב 4 — מעקב תגובות מייל

```bash
cd e:/system

# בדוק אם יש תגובות חדשות:
py -m outreach.reply_monitor poll

# הצג כל התגובות שהתקבלו:
py -m outreach.reply_monitor list

# הצג רק תגובות שלא טופלו:
py -m outreach.reply_monitor list --unread-only

# שלח תגובה חזרה לליד (לפי business_id):
py -m outreach.reply_monitor reply <ID> "הטקסט שלך"
```

---

## שלב 5 — סקריפט חיפוש מיילים (TODO)

כדי לאסוף מיילים אוטומטית לכל הלידים, צריך להוסיף לסקריפר:

```python
# scrapers/scraper.py — פונקציה קיימת: find_website_and_email(name, city)
# מחזירה (website_url, email) מ-Google Search
# להריץ על כל ליד ללא מייל:

from core.database import get_conn
from scrapers.scraper import find_website_and_email

conn = get_conn()
leads = conn.execute("SELECT id, name, city FROM businesses WHERE email IS NULL OR email=''").fetchall()
for lead in leads:
    try:
        _, email = find_website_and_email(lead['name'], lead['city'])
        if email:
            conn.execute("UPDATE businesses SET email=? WHERE id=?", (email, lead['id']))
            conn.commit()
            print(f"✅ {lead['name']}: {email}")
    except Exception as e:
        print(f"❌ {lead['name']}: {e}")
conn.close()
```

---

## סיכום — רצף עבודה מלא

```
1. הגדר App Password ב-.env
2. הרץ סריקת מיילים על הלידים
3. הרץ קמפיין מייל (dry_run=True לבדיקה)
4. הרץ קמפיין מייל (dry_run=False)
5. בדוק תגובות: py -m outreach.reply_monitor list --unread-only
```

---

## קבצים רלוונטיים

| קובץ | תפקיד |
|------|--------|
| `.env` | סיסמאות ומפתחות — לא עולה ל-GitHub |
| `outreach/leads_email_campaign.py` | שליחת מיילים ללידים |
| `outreach/reply_monitor.py` | מעקב תגובות IMAP |
| `core/database.py` | גישה לDB |
| `whatsapp-api/src/controllers/leads_campaign.controller.ts` | קמפיין ווצאפ |
