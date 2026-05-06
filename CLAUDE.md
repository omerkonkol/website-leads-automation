## WhatsApp Leads Campaign

כשהמשתמש אומר "שלח הודעות ללידים" / "תמשיך לשלוח" / "תריץ קמפיין" / "שלח עד X הודעות":
- שלח POST ל-http://localhost:3000/leads-campaign/send עם `{ "dailyLimit": N }`
- N לפי מה שביקש (ברירת מחדל: 50)
- הרץ ב-background עם `&` בסוף פקודת ה-curl
- אל תשאל שאלות — פשוט הרץ

עצירה: `POST http://localhost:3000/leads-campaign/stop`
בדיקה (dry run): הוסף `"dryRun": true` לבודי
טסט: הוסף `"testPhone": "05XXXXXXXX"` + `"testLeadId": N`
