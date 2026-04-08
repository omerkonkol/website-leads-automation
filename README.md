# Lead Generation System

## Project Structure

```
Entry Points:
  main.py                 - CLI: scrape, analyze, score, outreach
  dashboard.py            - Web dashboard (Streamlit)
  config.py               - Settings loader (.env)

Data Layer:
  database.py             - SQLite + Supabase sync, CRM operations
  db_engine.py            - Supabase REST API client
  lead_scorer.py          - Lead scoring engine (0-100)

Scraping (16 sources):
  scraper.py              - All scrapers: B144, Dapei Zahav, Google Maps,
                            Midrag, Easy, iGal, Freesearch, 2All, Wix,
                            Facebook, Zap, Google Search, Gov Registry,
                            Old Sites, Google Directories + competitor finder
  facebook_scraper.py     - Selenium-based Facebook scraper

Analysis:
  analyzer.py             - Website quality analysis (SSL, CMS, SEO, speed)
  business_verifier.py    - Activity verification (Google, WhatsApp)

Outreach:
  outreach_engine.py      - Send WhatsApp / Email campaigns
  email_sender.py         - Gmail SMTP sender
  whatsapp_sender.py      - WhatsApp Web automation
  pitch_builder.py        - Personalized message generator

Demo Generation:
  demo_generator.py       - Auto-generate demo websites for leads
  template_engine.py      - HTML template builder

Automation:
  scheduler.py            - Automated scheduling (scrape, outreach, follow-ups)

Config:
  .env                    - Secrets (not in git)
  .env.example            - Template for .env
  config.example.py       - Old config template
  requirements.txt        - Python dependencies
  .streamlit/             - Streamlit Cloud config
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env     # Fill in your keys
python main.py           # Run scraper + analyzer
streamlit run dashboard.py  # Open dashboard
```

## Dashboard (Live)

https://website-leads-automation-mysg7963ieaahyvpa5pppx.streamlit.app/
