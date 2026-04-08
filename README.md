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

## Live Dashboard
https://website-leads-automation-mysg7963ieaahyvpa5pppx.streamlit.app/

## Portfolio Site
https://portfolio-site-psi-vert.vercel.app/
