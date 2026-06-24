---
name: system-folder-layout
description: "How e:\\system root is organized — where client sites, archives, and assets live"
metadata: 
  node_type: memory
  type: project
  originSessionId: 76a86693-fb1a-4bf6-b8c6-6e0816cfecfa
---

ב-2026-06-04 סודר השורש של `e:\system`. מבנה מוסכם (שמור עליו — אל תפזר קבצים בשורש):

- **שורש** = רק האפליקציה החיה: `config.py`, `main.py`, `dashboard.py`, `leads.db`, `Procfile`, `railway.json`, `README.md`, וחבילות הקוד (`core/`, `scrapers/`, `analysis/`, `outreach/`, `generators/`, `scripts/`, `portfolio-site/`, `whatsapp-api/`, `leads-landing-pages/`).
- **`sites/`** — כל אתרי הלקוח/פרויקטים: nova-digital, nova-digital-v2, hadad-law, demo_trainer, demos, _pz, clients/. אתרים מועתקים תחת `sites/cloned/`.
- **`assets/`** — כל התמונות: `ads/`, `examples/`, `media/`, `misc/`.
- **`archive/`** — `scripts/` (סקריפטים חד-פעמיים), `db-backups/`, `data/`.

`sites/`, `archive/`, `assets/` כולם ב-`.gitignore` (לא חלק מה-repo). קבצים זמניים ולוגים נמחקים, לא נשמרים.
