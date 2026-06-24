---
name: WhatsApp Campaign Server
description: שרת ה-WhatsApp לשליחת הודעות ללידים - איך להפעיל ואיך לשלוח
type: project
originSessionId: 84b5246e-6b6c-4056-9512-b1062bfd4d41
---
שרת WhatsApp API לשליחת הודעות ללידים נמצא ב-`e:\system\whatsapp-api\`.

**How to apply:** לפני שליחת הודעות — לוודא שהשרת רץ על פורט 3000.

## הפעלת השרת

```powershell
cd e:\system\whatsapp-api
npm start   # אם כבר compiled (dist/ קיים)
# או:
npx ts-node src/index.ts   # dev mode
```

בדיקה שהשרת עולה: `curl http://localhost:3000/health`

## שליחת קמפיין

```bash
curl -X POST http://localhost:3000/api/leads-campaign/send \
  -H "Content-Type: application/json" \
  -d '{"dailyLimit": 350}'
```

עצירה: `POST http://localhost:3000/api/leads-campaign/stop`
בדיקת בריאות: `GET http://localhost:3000/api/health`

Dry run: הוסף `"dryRun": true`

טסט: הוסף `"testPhone": "05XXXXXXXX"` + `"testLeadId": N`

**Why:** השרת לא עולה אוטומטית — צריך להפעיל ידנית לפני כל קמפיין.
