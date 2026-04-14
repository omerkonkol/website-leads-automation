# Lead Generation System

## Project Structure

```
e:/system/
│
├── main.py                  ← CLI entry point
├── dashboard.py             ← Web dashboard (Streamlit)
├── config.py                ← Settings (.env loader)
├── requirements.txt
├── .env                     ← Secrets (not in git)
├── .streamlit/              ← Streamlit Cloud config
│
├── core/                    ← Data layer
│   ├── database.py          ← SQLite + Supabase sync, CRM
│   ├── db_engine.py         ← Supabase REST API client
│   └── lead_scorer.py       ← Lead scoring engine (0-100)
│
├── scrapers/                ← Data sources (16 scrapers)
│   ├── scraper.py           ← B144, Dapei Zahav, Google Maps, Midrag,
│   │                          Easy, iGal, Freesearch, 2All, Wix,
│   │                          Facebook, Zap, Google Search, Gov,
│   │                          Old Sites, Directories + enrichment
│   └── facebook_scraper.py  ← Selenium Facebook scraper
│
├── analysis/                ← Website analysis
│   ├── analyzer.py          ← SSL, CMS, SEO, speed, quality
│   └── business_verifier.py ← Activity verification
│
├── outreach/                ← Sending messages
│   ├── outreach_engine.py   ← Campaign manager
│   ├── email_sender.py      ← Gmail SMTP
│   ├── whatsapp_sender.py   ← WhatsApp Web automation
│   └── pitch_builder.py     ← Personalized messages
│
├── generators/              ← Demo site generation
│   ├── demo_generator.py    ← Auto-generate demo sites
│   ├── template_engine.py   ← HTML templates
│   └── scheduler.py         ← Automated scheduling
│
├── portfolio-site/          ← Next.js portfolio (Vercel)
│
└── assets/                  ← Images, exports (not in git)
```

Root-level .py files are redirect stubs — actual code is in subfolders.
All existing imports (`from database import ...`) continue to work.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env     # Fill in your keys
python main.py           # Run scraper + analyzer
streamlit run dashboard.py  # Open dashboard
```

## WhatsApp API

A Node.js/TypeScript server that sends WhatsApp messages via `whatsapp-web.js`. The dashboard connects to this API for all WhatsApp sending (both single and bulk).

### Setup

```bash
cd whatsapp-api
npm install
npm run build    # compile TypeScript → dist/
npm start        # run the server on port 3000
```

On first run, a **QR code** will appear in the terminal — scan it with WhatsApp on your phone to authenticate. The session is saved in `whatsapp-api/session_data/` so you only need to scan once.

### Architecture

```
whatsapp-api/
├── src/
│   ├── index.ts                    ← Express server, port 3000
│   ├── services/
│   │   └── whatsapp.service.ts     ← WhatsApp client (whatsapp-web.js + Puppeteer)
│   ├── controllers/
│   │   └── campaign.controller.ts  ← Send logic, rate limiting, anti-ban
│   ├── routes/
│   │   └── campaign.ts             ← Route definitions
│   └── utils/
│       ├── excel.ts                ← Excel parsing (exceljs)
│       └── sleep.ts                ← Random delays between messages
└── dist/                           ← Compiled JS (git-ignored)
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check — returns WhatsApp connection status |
| `POST` | `/api/campaign/send` | Send campaign from `.xlsx` file upload |
| `POST` | `/api/campaign/send-json` | Send campaign from JSON body (used by dashboard) |

### JSON Send Endpoint

`POST /api/campaign/send-json`

**Request body:**
```json
{
  "leads": [
    { "id": 1, "name": "Business Name", "phone": "0501234567", "message": "..." },
    { "id": 2, "name": "Another Biz", "phone": "0529876543", "message": "..." }
  ]
}
```

**Response (200):**
```json
{
  "sent": 2,
  "failed": 0,
  "total": 2,
  "dailySent": 5,
  "results": [
    { "id": 1, "phone": "0501234567", "status": "sent" },
    { "id": 2, "phone": "0529876543", "status": "sent" }
  ]
}
```

**Error responses:**
- `400` — Missing or empty leads array
- `429` — Daily send limit reached (default: 80/day)
- `503` — WhatsApp client not connected (scan QR)

### Anti-Ban Protections

- **Daily limit**: 80 messages/day (resets at midnight)
- **Batch limit**: 40 messages per request
- **Random delays**: between each message
- **Coffee breaks**: longer pause every 5 messages
- **Personalized messages**: `{{name}}` placeholders make each message unique

### Dashboard Integration

The dashboard uses the WhatsApp API in two places:

1. **"📨 שלח הודעות" tab** — Bulk send to selected leads. Loads all leads with Israeli mobile numbers (05x) that have a `whatsapp_pitch` in the DB. Supports filtering by send status and lead score, manual or select-all, and updates the DB after sending.

2. **"🚀 פעולות" tab** — Single lead send. Shows the personalized pitch with a send button. Also goes through the API.

Both paths update `whatsapp_sent`, `whatsapp_sent_at` in the `businesses` table and log to `outreach_log` on success.

### Running Both Services

You need two terminals:

```bash
# Terminal 1 — Dashboard
streamlit run dashboard.py

# Terminal 2 — WhatsApp API
cd whatsapp-api && npm start
```

The dashboard checks API availability and shows clear error messages if the server is down or WhatsApp is disconnected.

## Live Dashboard
https://website-leads-automation-mysg7963ieaahyvpa5pppx.streamlit.app/

## Portfolio Site
https://portfolio-site-psi-vert.vercel.app/
