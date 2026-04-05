"""
main.py — מנהל תהליך הסריקה, ניתוח, ושליחת פניות.
הרצה: python main.py
"""

import sys
import json
import time

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    SEARCH_QUERIES, MIN_QUALITY_SCORE, PORTFOLIO_LINKS
)
from database import (
    init_db, business_exists, insert_business,
    get_pending_outreach, export_to_excel, get_stats
)
from scraper import scrape_businesses, enrich_from_website
from analyzer import analyze_website
from pitch_builder import build_whatsapp_pitch, build_full_pitch, build_sales_summary


# ════════════════════════════════════════════════════════════════
#  שלב 1 + 2 — סריקה + ניתוח
# ════════════════════════════════════════════════════════════════
def run_scrape_and_analyze():
    """מריץ סריקת Google Maps וניתוח אתרים לכל השאילתות ב-config."""
    print("\n" + "="*60)
    print("  שלב 1-2: סריקת עסקים + ניתוח אתרים")
    print("="*60)

    new_count  = 0
    skip_count = 0

    for query in SEARCH_QUERIES:
        print(f"\n🔍 מחפש: {query}")
        businesses = scrape_businesses(query)

        for biz in businesses:
            name  = biz.get("name", "").strip()
            phone = biz.get("phone", "").strip()

            if not name:
                continue
            if business_exists(phone, name):
                print(f"  ⏭  דילוג (קיים): {name}")
                skip_count += 1
                continue

            # ── ניתוח האתר ──
            website = biz.get("website", "")
            print(f"  🔎 מנתח: {name} | {website or 'אין אתר'}")
            analysis = analyze_website(website)

            # ── העשרת נתונים מהאתר: מייל, פייסבוק, אינסטגרם ──
            enriched = enrich_from_website(website) if website else {}
            email    = biz.get("email") or enriched.get("email", "")
            fb_url   = enriched.get("facebook_url", "")
            ig_url   = enriched.get("instagram_url", "")
            city     = enriched.get("city") or biz.get("address", "").split()[-1] if biz.get("address") else ""

            if email:   print(f"     📧 מייל: {email}")
            if fb_url:  print(f"     👍 פייסבוק: {fb_url}")
            if ig_url:  print(f"     📸 אינסטגרם: {ig_url}")

            # ── הכנסה למסד הנתונים ──
            # ── בנה הודעות מכירה אישיות ──
            partial_biz = {
                "name": name, "website": website,
                **{k: analysis[k] for k in [
                    "has_website", "has_ssl", "is_responsive", "has_cta",
                    "has_form", "has_fb_pixel", "has_analytics", "load_time_ms",
                ]},
            }
            wa_pitch      = build_whatsapp_pitch(partial_biz)
            fp            = build_full_pitch(partial_biz)
            sales_summary = build_sales_summary(partial_biz)

            row = {
                "name":           name,
                "phone":          phone,
                "phone2":         biz.get("phone2", ""),
                "email":          email,
                "website":        website,
                "address":        biz.get("address", ""),
                "city":           city,
                "category":       biz.get("category", ""),
                "search_query":   biz.get("search_query", ""),
                "source":         biz.get("source", ""),
                "facebook_url":   fb_url,
                "instagram_url":  ig_url,
                "whatsapp_pitch": wa_pitch,
                "full_pitch":     fp,
                "sales_summary":  sales_summary,
                **{k: analysis[k] for k in [
                    "has_website", "has_ssl", "is_responsive",
                    "has_cta", "has_form", "has_fb_pixel",
                    "has_analytics", "load_time_ms", "quality_score"
                ]},
                "issues": json.dumps(analysis["issues"], ensure_ascii=False),
            }
            bid = insert_business(row)
            score = analysis["quality_score"]
            flag  = "🔥 ליד חם" if score >= 7 else ("👍 ליד טוב" if score >= MIN_QUALITY_SCORE else "➡️  ציון נמוך")
            print(f"     {flag} | ציון: {score}/10 | id={bid}")
            new_count += 1

            time.sleep(0.3)   # נימוס כלפי השרת

    print(f"\n✅ סריקה הסתיימה: {new_count} חדשים | {skip_count} דולגו")


# ════════════════════════════════════════════════════════════════
#  שלב 3 — ייצוא Excel
# ════════════════════════════════════════════════════════════════
def run_export():
    print("\n" + "="*60)
    print("  שלב 3: ייצוא ל-Excel")
    print("="*60)
    export_to_excel()


# ════════════════════════════════════════════════════════════════
#  שלב 4 — שליחת פניות
# ════════════════════════════════════════════════════════════════
def run_whatsapp():
    from whatsapp_sender import run_whatsapp_campaign
    print("\n" + "="*60)
    print("  שלב 4א: שליחת WhatsApp")
    print("="*60)
    pending = get_pending_outreach(min_score=MIN_QUALITY_SCORE, channel="whatsapp")
    print(f"  נמצאו {len(pending)} עסקים לשליחה (ציון ≥ {MIN_QUALITY_SCORE})")
    if not pending:
        print("  אין עסקים ממתינים לשליחת WhatsApp.")
        return
    run_whatsapp_campaign(pending, PORTFOLIO_LINKS)


def run_email():
    from email_sender import run_email_campaign
    print("\n" + "="*60)
    print("  שלב 4ב: שליחת מיילים")
    print("="*60)
    pending = get_pending_outreach(min_score=MIN_QUALITY_SCORE, channel="email")
    has_email = [b for b in pending if b.get("email")]
    print(f"  נמצאו {len(has_email)} עסקים עם מייל לשליחה")
    if not has_email:
        print("  אין עסקים עם כתובת מייל.")
        return
    run_email_campaign(has_email)


# ════════════════════════════════════════════════════════════════
#  תפריט ראשי
# ════════════════════════════════════════════════════════════════
def print_stats():
    stats = get_stats()
    print("\n📊 סטטיסטיקות מסד הנתונים:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


def main_menu():
    init_db()
    print_stats()

    while True:
        print("\n" + "═"*60)
        print("  מערכת לידים — בניית אתרים")
        print("═"*60)
        print("  1. סרוק עסקים חדשים (Google Maps) + נתח אתרים")
        print("  2. ייצא ל-Excel")
        print("  3. שלח WhatsApp לעסקים ממתינים")
        print("  4. שלח מיילים לעסקים ממתינים")
        print("  5. הצג סטטיסטיקות")
        print("  6. הרץ הכל (סריקה → ניתוח → WhatsApp → מייל)")
        print("  0. יציאה")
        print("─"*60)

        choice = input("בחר אפשרות: ").strip()

        if choice == "1":
            run_scrape_and_analyze()
            run_export()
        elif choice == "2":
            run_export()
        elif choice == "3":
            run_whatsapp()
        elif choice == "4":
            run_email()
        elif choice == "5":
            print_stats()
        elif choice == "6":
            run_scrape_and_analyze()
            run_export()
            confirm = input("\nלשלוח WhatsApp עכשיו? (כן/לא): ").strip()
            if confirm in ("כן", "yes", "y"):
                run_whatsapp()
            confirm = input("לשלוח מיילים עכשיו? (כן/לא): ").strip()
            if confirm in ("כן", "yes", "y"):
                run_email()
        elif choice == "0":
            print("להתראות!")
            break
        else:
            print("בחירה לא תקינה, נסה שוב.")


if __name__ == "__main__":
    main_menu()
