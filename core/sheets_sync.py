"""
sheets_sync.py — סנכרון לידים ל-Google Sheets.

הגדרה חד-פעמית:
  1. console.cloud.google.com → צור פרויקט → הפעל Google Sheets API + Google Drive API
  2. IAM → Service Accounts → צור → הורד JSON → שמור כ-google_credentials.json
  3. צור Google Sheet ריק, שתף עם ה-email של ה-service account (Editor)
  4. ב-.env: GOOGLE_SHEET_ID=<id מה-URL>, GOOGLE_CREDENTIALS_FILE=google_credentials.json
"""

import json
import os

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

_RENAME = {
    "name": "שם עסק", "phone": "טלפון", "phone2": "טלפון 2",
    "email": "מייל", "website": "אתר", "address": "כתובת",
    "city": "עיר", "category": "קטגוריה", "source": "מקור",
    "lead_score": "ציון ליד", "quality_score": "ציון אתר",
    "has_website": "יש אתר", "cms_platform": "פלטפורמה",
    "seo_score": "SEO", "google_reviews": "ביקורות",
    "google_rating": "דירוג גוגל", "owner_name": "בעלים",
    "pipeline_stage": "שלב CRM", "deal_value": "שווי עסקה",
    "next_followup": "פולואפ הבא", "whatsapp_sent": "WA נשלח",
    "email_sent": "מייל נשלח", "followup_count": "מס׳ פולואפים",
    "blacklisted": "בלקליסט", "created_at": "נוצר ב",
}

_DISPLAY_COLS = [
    "שם עסק", "טלפון", "טלפון 2", "מייל", "אתר", "עיר", "קטגוריה",
    "מקור", "ציון ליד", "ציון אתר", "יש אתר", "פלטפורמה", "SEO",
    "ביקורות", "דירוג גוגל", "בעלים", "שלב CRM", "שווי עסקה",
    "פולואפ הבא", "WA נשלח", "מייל נשלח", "מס׳ פולואפים", "נוצר ב",
]


def _get_client():
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    elif os.path.exists(creds_file):
        creds = Credentials.from_service_account_file(creds_file, scopes=_SCOPES)
    else:
        raise FileNotFoundError(
            f"לא נמצאו credentials. שמור את קובץ ה-JSON של ה-service account כ-{creds_file} "
            "או הגדר GOOGLE_CREDENTIALS_JSON כ-env var."
        )
    return gspread.authorize(creds)


def sync_leads_to_sheet(businesses: list[dict]) -> str:
    """
    Uploads all leads to the Google Sheet defined by GOOGLE_SHEET_ID.
    Returns the sheet URL.
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("חסר GOOGLE_SHEET_ID ב-.env")

    client = _get_client()
    sh = client.open_by_key(sheet_id)
    ws = sh.sheet1

    active = [b for b in businesses if not b.get("blacklisted")]
    df = pd.DataFrame(active)
    df.rename(columns=_RENAME, inplace=True)

    cols = [c for c in _DISPLAY_COLS if c in df.columns]
    df = df[cols].fillna("")

    # Convert booleans / ints to readable text
    for col in ["יש אתר", "WA נשלח", "מייל נשלח", "בלקליסט"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: "כן" if v else "לא")

    ws.clear()
    ws.update([df.columns.tolist()] + df.values.tolist())

    # Bold header row
    ws.format("A1:Z1", {"textFormat": {"bold": True}})

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"
