"""
scraper.py — שליפת עסקים מ-Google Maps.
תומך ב-SerpApi (מומלץ) ובגירוד ישיר.
"""

import time
import re
import requests
from config import SERPAPI_KEY, MAX_RESULTS_PER_QUERY


def _clean_phone(raw: str) -> str:
    """מנקה מספר טלפון ומחזיר ספרות בלבד."""
    if not raw:
        return ""
    digits = re.sub(r"[^\d+]", "", str(raw))
    return digits


def scrape_via_serpapi(query: str) -> list[dict]:
    """
    שולף עסקים מ-Google Maps דרך SerpApi.
    מחזיר רשימת dict עם שם, טלפון, כתובת, אתר.
    """
    results = []
    params = {
        "engine":    "google_maps",
        "q":         query,
        "hl":        "he",
        "gl":        "il",
        "type":      "search",
        "api_key":   SERPAPI_KEY,
        "num":       MAX_RESULTS_PER_QUERY,
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [SerpApi] שגיאה בחיפוש '{query}': {e}")
        return results

    for place in data.get("local_results", []):
        phone   = _clean_phone(place.get("phone", ""))
        website = (place.get("website") or "").strip()
        results.append({
            "name":         place.get("title", "").strip(),
            "phone":        phone,
            "email":        "",          # Google Maps לא חושף מיילים ישירות
            "website":      website,
            "address":      place.get("address", "").strip(),
            "category":     place.get("type", "").strip(),
            "search_query": query,
        })
        if len(results) >= MAX_RESULTS_PER_QUERY:
            break

    print(f"  [SerpApi] '{query}' → {len(results)} עסקים")
    return results


def scrape_via_requests(query: str) -> list[dict]:
    """
    גיבוי: גירוד Google Maps דרך URL רגיל (ללא API key).
    פחות אמין — משתמש בו רק אם אין SERPAPI_KEY.
    """
    print(f"  [Scraper] גירוד ישיר עבור: {query}")
    encoded = requests.utils.quote(query)
    url = f"https://www.google.com/maps/search/{encoded}/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "he-IL,he;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        html = resp.text

        # חיפוש שמות עסקים מתוך ה-HTML (גוגל מוסר אותם ב-JSON מוטמע)
        names    = re.findall(r'"([^"]{3,60})"(?=,\[\[")', html)[:MAX_RESULTS_PER_QUERY]
        phones   = re.findall(r'(\+?972[\s\-]?\d[\d\s\-]{7,12}|0\d[\d\s\-]{7,9})', html)
        websites = re.findall(r'https?://(?!maps\.google|google\.|goo\.gl)[^\s"\'<>]{5,80}', html)

        results = []
        for i, name in enumerate(names):
            phone   = _clean_phone(phones[i]) if i < len(phones) else ""
            website = websites[i].rstrip('\\,') if i < len(websites) else ""
            results.append({
                "name":         name,
                "phone":        phone,
                "email":        "",
                "website":      website,
                "address":      "",
                "category":     "",
                "search_query": query,
            })
        print(f"  [Scraper] '{query}' → {len(results)} תוצאות (גירוד ישיר - פחות מדויק)")
        return results
    except Exception as e:
        print(f"  [Scraper] שגיאה: {e}")
        return []


def scrape_businesses(query: str) -> list[dict]:
    """
    נקודת כניסה ראשית — בוחר שיטת גירוד אוטומטית.
    """
    if SERPAPI_KEY and SERPAPI_KEY != "YOUR_SERPAPI_KEY_HERE":
        return scrape_via_serpapi(query)
    else:
        print("  [!] SERPAPI_KEY לא מוגדר — משתמש בגירוד ישיר (פחות מדויק)")
        return scrape_via_requests(query)


def extract_email_from_website(url: str) -> str:
    """מנסה לחלץ כתובת מייל מהאתר של העסק."""
    if not url:
        return ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        emails = re.findall(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            resp.text
        )
        # סנן מיילים של ספריות/מסגרות
        blacklist = ["example.com", "sentry.io", "googleapis", "w3.org", "schema.org"]
        for em in emails:
            if not any(b in em for b in blacklist):
                return em.lower()
    except Exception:
        pass
    return ""
