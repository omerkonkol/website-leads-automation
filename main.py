"""
main.py — מנהל תהליך הסריקה, ניתוח, ושליחת פניות.
הרצה: python main.py
"""

import sys
import json
import time

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    SEARCH_QUERIES, FACEBOOK_FOCUSED_QUERIES, MIN_QUALITY_SCORE, PORTFOLIO_LINKS
)
from database import (
    init_db, business_exists, insert_business, update_business,
    get_pending_outreach, export_to_excel, get_stats, sync_all_to_supabase
)
from scraper import scrape_businesses, scrape_facebook_no_website, enrich_from_website, find_website_and_email
from analyzer import analyze_website
from pitch_builder import build_whatsapp_pitch, build_full_pitch, build_sales_summary
from lead_scorer import compute_lead_score, score_tier_hebrew
from business_verifier import verify_business_quick, verify_business


# ════════════════════════════════════════════════════════════════
#  שלב 1 + 2 — סריקה + ניתוח
# ════════════════════════════════════════════════════════════════
def run_scrape_and_analyze():
    """מריץ סריקה מכל המקורות וניתוח אתרים לכל השאילתות."""
    print("\n" + "="*60)
    print("  שלב 1-2: סריקת עסקים + ניתוח אתרים")
    print("  מקורות: B144, דפי זהב, Yad2, Google, Wix, Facebook, רשם חברות, Zap")
    print("="*60)

    new_count  = 0
    skip_count = 0
    error_count = 0

    for query in SEARCH_QUERIES:
        print(f"\n🔍 מחפש: {query}")
        try:
            businesses = scrape_businesses(query)
        except Exception as e:
            print(f"  ❌ שגיאה בסריקה: {e}")
            error_count += 1
            continue

        for biz in businesses:
            name  = biz.get("name", "").strip()
            phone = biz.get("phone", "").strip()

            if not name:
                continue
            if business_exists(phone, name):
                skip_count += 1
                continue

            # ── סינון: חייב טלפון ──
            if not phone:
                print(f"  ⏭️  דולג: {name} — אין מספר טלפון")
                skip_count += 1
                continue

            # ── אימות פעילות מהיר (לפני ניתוח כבד) ──
            quick_check = verify_business_quick(biz)
            if not quick_check["is_likely_active"] and quick_check["activity_score"] < 20:
                print(f"  ⏭️  דולג: {name} — {quick_check['summary']}")
                skip_count += 1
                continue

            # ── ניתוח האתר ──
            website = biz.get("website", "")
            print(f"  🔎 מנתח: {name} | {website or 'אין אתר'} [{biz.get('source','')}]")

            try:
                analysis = analyze_website(website)
            except Exception as e:
                print(f"     ❌ שגיאה בניתוח: {e}")
                analysis = {"has_website": 0, "has_ssl": 0, "is_responsive": 0,
                            "has_cta": 0, "has_form": 0, "has_fb_pixel": 0,
                            "has_analytics": 0, "load_time_ms": None,
                            "quality_score": 0, "issues": ["שגיאה בניתוח"],
                            "has_title_tag": 0, "has_meta_desc": 0, "has_h1": 0,
                            "has_robots_txt": 0, "has_sitemap": 0, "seo_score": None,
                            "cms_platform": None, "copyright_year": None,
                            "pagespeed_score": None, "core_web_vitals": None}

            # ── העשרת נתונים מהאתר ──
            enriched = enrich_from_website(website) if website else {}
            email    = biz.get("email") or enriched.get("email", "")
            fb_url   = biz.get("facebook_url", "") or enriched.get("facebook_url", "")
            ig_url   = enriched.get("instagram_url", "")
            li_url   = enriched.get("linkedin_url", "")
            city     = biz.get("city") or enriched.get("city") or ""
            if not city and biz.get("address"):
                city = biz["address"].split()[-1] if biz["address"].strip() else ""

            if email:   print(f"     📧 מייל: {email}")
            if fb_url:  print(f"     👍 פייסבוק: {fb_url}")

            # ── אם אין מייל/אתר — חפש ב-Google ──
            if not email or not website:
                print(f"     🔍 מחפש מידע נוסף ב-Google...")
                found = find_website_and_email(name, city)
                if found.get("email") and not email:
                    email = found["email"]
                    print(f"     📧 נמצא מייל: {email}")
                if found.get("website") and not website:
                    website = found["website"]
                    biz["website"] = website
                    print(f"     🌐 נמצא אתר: {website}")
                    try:
                        analysis = analyze_website(website)
                    except Exception:
                        pass
                if found.get("facebook_url") and not fb_url:
                    fb_url = found["facebook_url"]

            # ── אימות פעילות מלא (כולל Google + WhatsApp) ──
            full_biz = {**biz, "email": email, "facebook_url": fb_url, "website": website}
            verification = verify_business(full_biz)
            if not verification["is_likely_active"]:
                print(f"     ⏭️  דולג: {verification['summary']}")
                skip_count += 1
                continue
            print(f"     ✅ פעילות: {verification['activity_score']}/100 — {verification['summary']}")

            # ── הודעות מכירה אישיות ──
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

            # ── הכנסה למסד הנתונים ──
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
                "fb_followers":   biz.get("fb_followers", 0),
                "fb_snippet_has_website": 1 if biz.get("fb_snippet_has_website") else 0,
                "whatsapp_pitch": wa_pitch,
                "full_pitch":     fp,
                "sales_summary":  sales_summary,
                # ניתוח בסיסי
                **{k: analysis[k] for k in [
                    "has_website", "has_ssl", "is_responsive",
                    "has_cta", "has_form", "has_fb_pixel",
                    "has_analytics", "load_time_ms", "quality_score"
                ]},
                "issues": json.dumps(analysis["issues"], ensure_ascii=False),
                # ניתוח מתקדם
                "cms_platform":   analysis.get("cms_platform"),
                "seo_score":      analysis.get("seo_score"),
                "has_title_tag":  analysis.get("has_title_tag", 0),
                "has_meta_desc":  analysis.get("has_meta_desc", 0),
                "has_h1":         analysis.get("has_h1", 0),
                "has_robots_txt": analysis.get("has_robots_txt", 0),
                "has_sitemap":    analysis.get("has_sitemap", 0),
                "copyright_year": analysis.get("copyright_year"),
                "pagespeed_score": analysis.get("pagespeed_score"),
                "core_web_vitals": analysis.get("core_web_vitals"),
                # Google reviews (אם הגיעו מהמקור)
                "google_reviews": biz.get("google_reviews"),
                "google_rating":  biz.get("google_rating"),
                # אימות פעילות
                "activity_score":    verification["activity_score"],
                "is_likely_active":  1,  # רק פעילים מגיעים לכאן
                "activity_details":  json.dumps(verification["reasons"], ensure_ascii=False),
            }
            bid = insert_business(row)

            # ── חשב ציון ליד מסחרי ──
            lead_score, breakdown = compute_lead_score({**row, "id": bid})
            update_business(bid, {"lead_score": lead_score})

            tier  = score_tier_hebrew(lead_score)
            score = analysis["quality_score"]
            cms   = analysis.get("cms_platform") or ""
            seo   = analysis.get("seo_score") or ""
            print(f"     {tier} | ליד: {lead_score}/100 | אתר: {score}/10 | CMS: {cms} | SEO: {seo} | id={bid}")
            new_count += 1

            time.sleep(0.3)

    print(f"\n✅ סריקה הסתיימה: {new_count} חדשים | {skip_count} דולגו | {error_count} שגיאות")


# ════════════════════════════════════════════════════════════════
#  מצב מהיר — סריקת פייסבוק ממוקדת (לידים חמים)
# ════════════════════════════════════════════════════════════════
def run_facebook_focused():
    """
    סריקה ממוקדת לעסקי פייסבוק ללא אתר — הלידים הכי חמים.
    מהיר יותר: דולג ניתוח אתר מפורט לעסקים ללא אתר.
    """
    print("\n" + "="*60)
    print("  🎯 מצב פייסבוק ממוקד — לידים חמים בלבד")
    print("  מחפש עסקים שפעילים בפייסבוק ואין להם אתר")
    print("="*60)

    new_count = 0
    skip_count = 0

    for category, city in FACEBOOK_FOCUSED_QUERIES:
        print(f"\n🔍 פייסבוק: {category} ב{city}")
        try:
            businesses = scrape_facebook_no_website(category, city)
        except Exception as e:
            print(f"  ❌ שגיאה: {e}")
            continue

        for biz in businesses:
            name  = biz.get("name", "").strip()
            phone = biz.get("phone", "").strip()

            if not name:
                continue
            if business_exists(phone, name):
                skip_count += 1
                continue

            # עבור עסקי פייסבוק ללא אתר — אין צורך בניתוח כבד
            fb_has_website = biz.get("fb_snippet_has_website", False)
            website = biz.get("website", "")

            analysis = {
                "has_website": 1 if website else 0,
                "has_ssl": 0, "is_responsive": 0, "has_cta": 0,
                "has_form": 0, "has_fb_pixel": 0, "has_analytics": 0,
                "load_time_ms": None, "quality_score": 0,
                "issues": ["עסק פייסבוק — לא נותח"],
                "has_title_tag": 0, "has_meta_desc": 0, "has_h1": 0,
                "has_robots_txt": 0, "has_sitemap": 0, "seo_score": None,
                "cms_platform": None, "copyright_year": None,
                "pagespeed_score": None, "core_web_vitals": None,
            }

            # אם יש אתר — נתח אותו
            if website and fb_has_website:
                print(f"  🔎 {name} — יש אתר, מנתח...")
                try:
                    analysis = analyze_website(website)
                except Exception:
                    pass

            fb_url = biz.get("facebook_url", "")
            city_biz = biz.get("city") or city

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
                "phone2":         "",
                "email":          "",
                "website":        website,
                "address":        "",
                "city":           city_biz,
                "category":       category,
                "search_query":   f"{category} {city}",
                "source":         "facebook",
                "facebook_url":   fb_url,
                "instagram_url":  "",
                "fb_followers":   biz.get("fb_followers", 0),
                "fb_snippet_has_website": 1 if fb_has_website else 0,
                "whatsapp_pitch": wa_pitch,
                "full_pitch":     fp,
                "sales_summary":  sales_summary,
                **{k: analysis[k] for k in [
                    "has_website", "has_ssl", "is_responsive",
                    "has_cta", "has_form", "has_fb_pixel",
                    "has_analytics", "load_time_ms", "quality_score"
                ]},
                "issues": json.dumps(analysis["issues"], ensure_ascii=False),
                "cms_platform":    analysis.get("cms_platform"),
                "seo_score":       analysis.get("seo_score"),
                "has_title_tag":   analysis.get("has_title_tag", 0),
                "has_meta_desc":   analysis.get("has_meta_desc", 0),
                "has_h1":          analysis.get("has_h1", 0),
                "has_robots_txt":  analysis.get("has_robots_txt", 0),
                "has_sitemap":     analysis.get("has_sitemap", 0),
                "copyright_year":  analysis.get("copyright_year"),
                "pagespeed_score": analysis.get("pagespeed_score"),
                "core_web_vitals": analysis.get("core_web_vitals"),
                "activity_score":  60,  # פעיל בפייסבוק = מינימום 60
                "is_likely_active": 1,
                "activity_details": json.dumps(["נמצא בפייסבוק"], ensure_ascii=False),
            }
            bid = insert_business(row)
            lead_score, _ = compute_lead_score({**row, "id": bid})
            update_business(bid, {"lead_score": lead_score})

            tier = score_tier_hebrew(lead_score)
            no_site = "ללא אתר" if not fb_has_website else "יש אתר"
            followers = biz.get("fb_followers", 0)
            print(f"     {tier} | ליד: {lead_score}/100 | {no_site} | עוקבים: {followers} | id={bid}")
            new_count += 1
            time.sleep(0.2)

    print(f"\n✅ פייסבוק ממוקד: {new_count} לידים חדשים | {skip_count} דולגו")


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
        print("  מערכת לידים — בניית אתרים (מתקדם)")
        print("═"*60)
        print("  1. סרוק עסקים חדשים (10 מקורות) + נתח אתרים")
        print("  🎯 F. סריקת פייסבוק ממוקדת — לידים חמים (מהיר!)")
        print("  2. ייצא ל-Excel")
        print("  3. שלח WhatsApp לעסקים ממתינים")
        print("  4. שלח מיילים לעסקים ממתינים")
        print("  5. הצג סטטיסטיקות")
        print("  6. הרץ הכל (סריקה → ניתוח → WhatsApp → מייל)")
        print("  7. ניתוח מחדש לכל הלידים הישנים")
        print("  8. עדכן ציוני לידים")
        print("  9. הפעל scheduler (רקע)")
        print("  🔵 FB. סריקת פייסבוק ישירה (Selenium — הלידים הכי טובים)")
        print("  ☁️  S. סנכרן הכל ל-Supabase (דשבורד משותף)")
        print("  0. יציאה")
        print("─"*60)

        choice = input("בחר אפשרות: ").strip()

        if choice in ("f", "F", "פ"):
            run_facebook_focused()
            run_export()
        elif choice == "1":
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
        elif choice == "7":
            from scheduler import run_weekly_reanalysis
            run_weekly_reanalysis()
        elif choice == "8":
            from lead_scorer import rescore_all
            n = rescore_all()
            print(f"  ✅ עודכנו {n} ציוני לידים")
        elif choice == "9":
            from scheduler import run_daemon
            run_daemon()
        elif choice in ("fb", "FB"):
            from facebook_scraper import run_facebook_scan
            run_facebook_scan(FACEBOOK_FOCUSED_QUERIES)
        elif choice in ("s", "S", "ס"):
            print("\n☁️  מסנכרן את כל הלידים ל-Supabase...")
            n = sync_all_to_supabase()
            if n:
                print(f"  ✅ {n} לידים סונכרנו — הדשבורד המשותף מעודכן")
        elif choice == "0":
            print("להתראות!")
            break
        else:
            print("בחירה לא תקינה, נסה שוב.")


if __name__ == "__main__":
    main_menu()
