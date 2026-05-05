"""
leads_landing_v2.py — premium per-lead landing page generator (Foreman design language).

Reads no-website leads from leads.db, generates a dark-theme premium landing page
for each, and writes a manifest CSV that the WhatsApp campaign reads.

Design language inspired by `claude.ai/design` Foreman handoff bundle:
- Dark theme (#0A0A0B), per-category accent color.
- Geist (display) + Inter (body) + Geist Mono (labels).
- Massive editorial hero typography, refined CTAs with glow.
- Bento grid, problem list, how-it-works, real testimonials, premium pricing card.
- Subtle grain + radial gradients, no fake WhatsApp mockups, no repeated icons.

Per-lead data used (when present in DB):
- google_rating + google_reviews → trust pill, hero stat
- services (JSON array) → real services in features section
- opening_hours (JSON object) → "when we're open" tile

Output:
    leads-landing-pages/
        index.html
        _redirects
        manifest.csv
        l/<slug>-<id>/index.html

Run:
    python generators/leads_landing_v2.py
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple

try:
    from .leads_icons import svg as svg_icon, ICON_LIB  # type: ignore
except ImportError:
    from leads_icons import svg as svg_icon, ICON_LIB  # type: ignore

# ── Per-category accent + icon-key (Lucide SVG, not emoji) ─────────────
CATEGORY_STYLE: dict[str, tuple[str, str]] = {
    "מוסך":              ("#dc2626", "car"),
    "מסעדה":             ("#ea580c", "utensils"),
    "פיצרייה":           ("#dc2626", "pizza"),
    "פיצריה":            ("#dc2626", "pizza"),
    "קפה":               ("#a16207", "coffee"),
    "בית קפה":           ("#a16207", "coffee"),
    "קונדיטוריה":        ("#d97706", "cake"),
    "קוסמטיקה":          ("#9333ea", "sparkles"),
    "קוסמטיקאית":        ("#9333ea", "sparkles"),
    "מכון יופי":         ("#9333ea", "sparkles"),
    "סלון מניקור":       ("#db2777", "spray"),
    "סלון מניקור ופדיקור":("#db2777", "spray"),
    "מספרה":             ("#2563eb", "scissors"),
    "ברבר":              ("#1e40af", "scissors"),
    "סלון":              ("#3b82f6", "scissors"),
    "שיפוצים":           ("#16a34a", "hammer"),
    "שרברב":             ("#0891b2", "shower"),
    "אינסטלטור":         ("#0891b2", "shower"),
    "חשמלאי":            ("#ca8a04", "zap"),
    "עורך דין":          ("#0ea5e9", "scale"),
    "משרד עורכי דין":    ("#0ea5e9", "scale"),
    "נוטריון":           ("#0284c7", "stamp"),
    "רואה חשבון":        ("#0d9488", "calculator"),
    "מרפאת שיניים":      ("#06b6d4", "tooth"),
    "רופא שיניים":       ("#06b6d4", "tooth"),
    "מרפאה":             ("#10b981", "stethoscope"),
    "מורה פרטית":        ("#7c3aed", "book"),
    "מורה פרטי":         ("#7c3aed", "book"),
    "מאמן כושר":         ("#dc2626", "dumbbell"),
    "צילום":             ("#f59e0b", "camera"),
    "אולם אירועים":      ("#be185d", "party"),
    "פרחים":             ("#16a34a", "flower"),
    "סופרמרקט":          ("#16a34a", "cart"),
    "חנות בגדים":        ("#db2777", "shirt"),
    "וטרינר":            ("#0891b2", "paw"),
    "סטודיו":            ("#7c3aed", "palette"),
    "אופטיקה":           ("#0ea5e9", "glasses"),
}
DEFAULT_STYLE = ("#FF5722", "building")

# Per-category hero photo — Unsplash (free, royalty-free).
CATEGORY_IMAGE_ID: dict[str, str] = {
    "עורך דין":            "photo-1505664194779-8beaceb93744",
    "משרד עורכי דין":      "photo-1505664194779-8beaceb93744",
    "נוטריון":             "photo-1450101499163-c8848c66ca85",
    "רואה חשבון":          "photo-1554224155-8d04cb21cd6c",
    "מרפאת שיניים":        "photo-1606811971618-4486d14f3f99",
    "רופא שיניים":         "photo-1606811971618-4486d14f3f99",
    "מרפאה":               "photo-1631815589968-fdb09a223b1e",
    "מסעדה":               "photo-1517248135467-4c7edcad34c4",
    "פיצרייה":             "photo-1513104890138-7c749659a591",
    "קפה":                "photo-1554118811-1e0d58224f24",
    "בית קפה":             "photo-1554118811-1e0d58224f24",
    "קונדיטוריה":          "photo-1509440159596-0249088772ff",
    "מספרה":               "photo-1521590832167-7bcbfaa6381f",
    "ברבר":                "photo-1503951914875-452162b0f3f1",
    "סלון":                "photo-1562322140-8baeececf3df",
    "מכון יופי":           "photo-1540555700478-4be289fbecef",
    "קוסמטיקה":            "photo-1571781926291-c477ebfd024b",
    "קוסמטיקאית":          "photo-1487412947147-5cebf100ffc2",
    "סלון מניקור":         "photo-1604654894610-df63bc536371",
    "סלון מניקור ופדיקור": "photo-1604654894610-df63bc536371",
    "שיפוצים":             "photo-1503387762-592deb58ef4e",
    "שרברב":               "photo-1607472586893-edb57bdc0e39",
    "אינסטלטור":           "photo-1607472586893-edb57bdc0e39",
    "חשמלאי":              "photo-1581092160562-40aa08e78837",
    "מוסך":                "photo-1486006920555-c77dcf18193c",
    "וטרינר":              "photo-1628009368231-7bb7cfcb0def",
    "מורה פרטית":          "photo-1481627834876-b7833e8f5570",
    "מורה פרטי":           "photo-1481627834876-b7833e8f5570",
    "מאמן כושר":           "photo-1534438327276-14e5300c3a48",
    "צילום":               "photo-1502920917128-1aa500764cbd",
    "אולם אירועים":        "photo-1519225421980-715cb0215aed",
    "פרחים":               "photo-1490750967868-88aa4486c946",
    "סופרמרקט":            "photo-1542838132-92c53300491e",
    "חנות בגדים":          "photo-1567401893414-76b7b1e5a7a5",
    "סטודיו":              "photo-1542744095-fcf48d80b0fd",
    "אופטיקה":             "photo-1577401239170-897942555fb3",
    "פיצריה":              "photo-1513104890138-7c749659a591",
}
DEFAULT_IMAGE_ID = "photo-1497366216548-37526070297c"  # generic interior

# Per-category services (icon, title, description). Different icon per service.
CATEGORY_SERVICES: dict[str, list[tuple[str, str, str]]] = {
    # (icon-key, title, description) — icon-key looked up in ICON_LIB
    "עורך דין": [
        ("scale", "דיני עבודה ונזיקין", "ייצוג וליווי משפטי בכל סוגי התביעות, מהפנייה הראשונית ועד פסק הדין."),
        ("building", "נדל\"ן וחוזים", "עריכת הסכמים, ליווי עסקאות, בדיקות נאותות ורישום זכויות."),
        ("users", "דיני משפחה", "גירושין, ירושה, צוואות והסכמי ממון בליווי דיסקרטי וקשוב."),
    ],
    "משרד עורכי דין": [
        ("scale", "דיני עבודה ונזיקין", "ייצוג וליווי משפטי בכל סוגי התביעות, מהפנייה הראשונית ועד פסק הדין."),
        ("building", "נדל\"ן וחוזים", "עריכת הסכמים, ליווי עסקאות, בדיקות נאותות ורישום זכויות."),
        ("users", "דיני משפחה", "גירושין, ירושה, צוואות והסכמי ממון בליווי דיסקרטי וקשוב."),
    ],
    "נוטריון": [
        ("stamp", "אישורים ואימותים", "אימות חתימה, תרגום ואישור מסמכים בכל השפות."),
        ("scroll", "צוואות והסכמים", "עריכה ואישור צוואות, הסכמי ממון וייפויי כוח."),
        ("mail", "מסמכים בינלאומיים", "אפוסטיל ואישור לכל שגרירות בעולם."),
    ],
    "רואה חשבון": [
        ("calculator", "ניהול חשבונות וספרים", "הנהלת חשבונות שוטפת לעצמאיים וחברות, פיקוח על דוחות."),
        ("building", "ייצוג מול רשויות", "ייעוץ מס וייצוג מול רשות המסים והביטוח הלאומי."),
        ("rocket", "ייעוץ עסקי", "תכנון מס, תקצוב, פיתוח עסקי וליווי שוטף."),
    ],
    "מרפאת שיניים": [
        ("tooth", "בדיקות וניקוי אבנית", "טיפולי שגרה לשמירה על בריאות הפה והחניכיים."),
        ("sparkles", "הלבנת שיניים", "טיפול אסתטי לחיוך מסנוור עם תוצאות מיידיות."),
        ("stethoscope", "שתלים וסתימות", "פתרונות לשיקום השיניים בטכנולוגיה הכי מתקדמת."),
    ],
    "רופא שיניים": [
        ("tooth", "בדיקות וניקוי אבנית", "טיפולי שגרה לשמירה על בריאות הפה והחניכיים."),
        ("sparkles", "הלבנת שיניים", "טיפול אסתטי לחיוך מסנוור עם תוצאות מיידיות."),
        ("stethoscope", "שתלים וסתימות", "פתרונות לשיקום השיניים בטכנולוגיה הכי מתקדמת."),
    ],
    "מוסך": [
        ("droplet", "טיפול שוטף", "החלפת שמן, מסננים, ובדיקה מקיפה לפני נסיעה."),
        ("car", "מערכת בלמים", "החלפת רפידות ודיסקיות באיכות פרימיום."),
        ("wrench", "אבחון תקלות", "אבחון מחשב וטיפול במנוע ובמערכת החשמל."),
    ],
    "מסעדה": [
        ("utensils", "מטבח ביתי וים-תיכוני", "מנות טריות מהשוק על אש איטית."),
        ("coffee", "בר ויינות", "מבחר משקאות ויינות מקומיים נבחרים."),
        ("party", "אירועים ומשלוחים", "אירוח קבוצות והזמנות עד הבית."),
    ],
    "פיצרייה": [
        ("pizza", "פיצות מיוחדות", "בצק תוצרת בית, רטבים ביתיים, תוספות פרימיום."),
        ("utensils", "תוספות ושתייה", "סלטים, פסטות ומגוון שתייה."),
        ("rocket", "משלוחים מהירים", "משלוח עד הבית תוך 30 דקות."),
    ],
    "מספרה": [
        ("scissors", "תספורות גברים ונשים", "סטייליסט מקצועי, חיתוך מודרני."),
        ("palette", "צביעה והבהרה", "טכניקות מתקדמות וטיפולים שומרי-צבע."),
        ("sparkles", "טיפולי שיער", "מסכות, החלקה וטיפולי בריאות לשיער."),
    ],
    "ברבר": [
        ("scissors", "תספורת גבר", "סטייל מודרני, יחס אישי."),
        ("razor", "גילוח קלאסי", "גילוח חם עם סכין מקצועי."),
        ("sparkles", "עיצוב זקן", "טיפוח ועיצוב הזקן."),
    ],
    "מכון יופי": [
        ("sparkles", "טיפולי פנים", "ניקוי עמוק, רענון ולחות לעור קורן."),
        ("zap", "הסרת שיער", "טכנולוגיית IPL ולייזר עדינה ויעילה."),
        ("heart", "עיצוב גבות וריסים", "Lifting, Tinting, ולמינציה."),
    ],
    "קוסמטיקאית": [
        ("sparkles", "טיפולי פנים", "ניקוי עמוק, רענון ולחות לעור קורן."),
        ("zap", "הסרת שיער", "טכנולוגיית IPL ולייזר עדינה ויעילה."),
        ("heart", "עיצוב גבות וריסים", "Lifting, Tinting, ולמינציה."),
    ],
    "סלון מניקור": [
        ("spray", "ג'ל ולק ג'ל", "עיצוב מקצועי שמחזיק שבועות."),
        ("droplet", "פדיקור רפואי", "טיפול בעקבים ובציפורניים."),
        ("palette", "ציורי ציפורניים", "עיצובים מותאמים אישית."),
    ],
    "סלון מניקור ופדיקור": [
        ("spray", "ג'ל ולק ג'ל", "עיצוב מקצועי שמחזיק שבועות."),
        ("droplet", "פדיקור רפואי", "טיפול בעקבים ובציפורניים."),
        ("palette", "ציורי ציפורניים", "עיצובים מותאמים אישית."),
    ],
    "שיפוצים": [
        ("hammer", "שיפוצים כלליים", "מקלחות, מטבחים, ריצוף וצבע."),
        ("calendar", "ייעוץ ותכנון", "ליווי מהשרטוט ועד המסירה."),
        ("sparkles", "עבודות גמר", "פרטים קטנים שעושים את ההבדל."),
    ],
    "שרברב": [
        ("shower", "פתיחת סתימות", "הגעה תוך שעה, ללא עלות נסיעה."),
        ("wrench", "התקנות וצנרת", "החלפת ברזים, אסלות ודודי שמש."),
        ("droplet", "איתור נזילות", "בדיקה מקיפה ותיקון מלא."),
    ],
    "אינסטלטור": [
        ("shower", "פתיחת סתימות", "הגעה תוך שעה, ללא עלות נסיעה."),
        ("wrench", "התקנות וצנרת", "החלפת ברזים, אסלות ודודי שמש."),
        ("droplet", "איתור נזילות", "בדיקה מקיפה ותיקון מלא."),
    ],
    "חשמלאי": [
        ("zap", "התקנות חשמל", "לוחות, שקעים, גופי תאורה."),
        ("search", "איתור תקלות", "אבחון ותיקון בעיות חשמל."),
        ("check", "בדיקות ותקינות", "בדיקות תקינות לפני קבלת טופס 4."),
    ],
    "וטרינר": [
        ("stethoscope", "בדיקות שגרה וחיסונים", "מעקב בריאותי תקופתי לחיות מחמד."),
        ("paw", "מרפאה דחופה", "מענה לבעיות בריאות חריפות."),
        ("scissors", "פעולות וניתוחים", "סטריליזציה, פעולות שיניים וניתוחים."),
    ],
    "מורה פרטית": [
        ("book", "מתמטיקה ופיזיקה", "הכנה למבחנים ובגרויות."),
        ("lightbulb", "עברית ואנגלית", "ביטוי, הבנה והכנה לפסיכומטרי."),
        ("mortarboard", "ליווי שיעורים", "סיוע שוטף לאורך השנה."),
    ],
    "מורה פרטי": [
        ("book", "מתמטיקה ופיזיקה", "הכנה למבחנים ובגרויות."),
        ("lightbulb", "עברית ואנגלית", "ביטוי, הבנה והכנה לפסיכומטרי."),
        ("mortarboard", "ליווי שיעורים", "סיוע שוטף לאורך השנה."),
    ],
    "מאמן כושר": [
        ("dumbbell", "אימון אישי", "תכנית מותאמת לרמה ולמטרות."),
        ("heart", "תזונה והרזיה", "ליווי תזונתי לתוצאות מוכחות."),
        ("users", "אימון קבוצתי", "מסלול קבוצתי בהשראה ובמוטיבציה."),
    ],
    "צילום": [
        ("camera", "צילומי אירועים", "חתונות, בריתות, ובר/בת מצווה."),
        ("users", "צילומי משפחה", "סשנים בסטודיו או חוץ."),
        ("trophy", "צילום עסקי", "תדמית, מוצרים וסרטוני קידום."),
    ],
    "אולם אירועים": [
        ("party", "חתונות", "אולם מעוצב לאירועים יוקרתיים."),
        ("cake", "ימי הולדת", "אירועים פרטיים לכל גיל."),
        ("building", "כנסים ועסקי", "תשתית טכנית מלאה לאירועי עבודה."),
    ],
    "פרחים": [
        ("flower", "זרי כלה", "עיצוב מותאם אישית."),
        ("party", "הזמנות לאירועים", "סידורים יוקרתיים."),
        ("rocket", "משלוחי פרחים", "משלוחים בכל הארץ."),
    ],
    "סופרמרקט": [
        ("cart", "פירות וירקות טריים", "מהשוק ישירות אליכם."),
        ("shopping", "מוצרי חלב ומאפים", "מבחר רחב לכל יום."),
        ("rocket", "משלוחים", "משלוח לבית עם הזמנה אונליין."),
    ],
    "חנות בגדים": [
        ("shirt", "בגדי נשים וגברים", "מותגים מובחרים בכל קולקציה."),
        ("shopping", "אקססוריז", "תיקים, נעליים ותכשיטים."),
        ("tag", "מתנות וקופונים", "אריזות מתנה ושוברים."),
    ],
    "קונדיטוריה": [
        ("cake", "עוגות אירועים", "ימי הולדת, חתונות ואירועים."),
        ("sparkles", "עוגיות וקאפקייקס", "עיצובים מותאמים אישית."),
        ("coffee", "מאפים טריים", "מאפים נאפים בכל בוקר."),
    ],
    "קפה": [
        ("coffee", "קפה איכותי", "פולים נבחרים, חליטה מקצועית."),
        ("cake", "מאפים ובוקר", "מאפים טריים מדי בוקר."),
        ("utensils", "ארוחות קלות", "סלטים, סנדוויצ'ים ומנות יום."),
    ],
    "בית קפה": [
        ("coffee", "קפה איכותי", "פולים נבחרים, חליטה מקצועית."),
        ("cake", "מאפים ובוקר", "מאפים טריים מדי בוקר."),
        ("utensils", "ארוחות קלות", "סלטים, סנדוויצ'ים ומנות יום."),
    ],
    "סטודיו": [
        ("palette", "עיצוב וייעוץ", "ליווי מקצועי מהקונספט עד הביצוע."),
        ("sparkles", "עבודות מותאמות", "פתרונות אישיים לכל לקוח."),
        ("heart", "שירות לאורך זמן", "ליווי גם לאחר סיום הפרויקט."),
    ],
}
DEFAULT_SERVICES: list[tuple[str, str, str]] = [
    ("star", "שירות מקצועי", "ניסיון של שנים בתחום."),
    ("heart", "ליווי אישי", "תשומת לב לכל לקוח."),
    ("check", "מחיר הוגן", "שקיפות ושירות ללא הפתעות."),
]
SERVICE_ICON_POOL = ["star", "target", "zap", "trophy", "wrench", "heart", "check", "rocket", "calendar", "lightbulb"]

# Per-category Final CTA — (lead question, accent answer)
CATEGORY_FINAL_CTA: dict[str, tuple[str, str]] = {
    "עורך דין":            ("צריכים ייצוג משפטי?", "אנחנו לרשותכם."),
    "משרד עורכי דין":      ("צריכים ייצוג משפטי?", "אנחנו לרשותכם."),
    "נוטריון":             ("צריכים אישור נוטריוני?", "נטפל בזה במהירות."),
    "רואה חשבון":          ("צריכים סדר בחשבונאות?", "בואו נתחיל."),
    "מרפאת שיניים":        ("מוכנים לחיוך חדש?", "קבעו תור."),
    "רופא שיניים":         ("מוכנים לחיוך חדש?", "קבעו תור."),
    "מרפאה":               ("צריכים בדיקה רפואית?", "קבעו תור עכשיו."),
    "מסעדה":               ("רעבים?", "בואו לטעום אצלנו."),
    "פיצרייה":             ("רעבים לפיצה?", "הזמינו עכשיו."),
    "פיצריה":              ("רעבים לפיצה?", "הזמינו עכשיו."),
    "קפה":                 ("יש לכם 5 דקות?", "בואו לקפה."),
    "בית קפה":             ("יש לכם 5 דקות?", "בואו לקפה."),
    "קונדיטוריה":          ("יש לכם אירוע?", "נכין לכם משהו מתוק."),
    "מספרה":               ("מוכנים לסטייל חדש?", "קבעו תור."),
    "ברבר":                ("מוכנים לסטייל חדש?", "קבעו תור."),
    "סלון":                ("מוכנים לסטייל חדש?", "קבעו תור."),
    "מכון יופי":           ("מוכנים להתפנק?", "קבעו תור."),
    "קוסמטיקה":            ("מוכנים להתפנק?", "קבעו תור."),
    "קוסמטיקאית":          ("מוכנים להתפנק?", "קבעו תור."),
    "סלון מניקור":         ("רוצים ציפורניים מושלמות?", "קבעו תור."),
    "סלון מניקור ופדיקור": ("רוצים ציפורניים מושלמות?", "קבעו תור."),
    "שיפוצים":             ("יש לכם פרויקט בראש?", "בואו נדבר."),
    "שרברב":               ("יש לכם תקלה?", "אנחנו בדרך."),
    "אינסטלטור":           ("יש לכם תקלה?", "אנחנו בדרך."),
    "חשמלאי":              ("צריכים חשמלאי?", "אנחנו זמינים."),
    "מוסך":                ("האוטו זקוק לטיפול?", "בואו נטפל בו."),
    "וטרינר":              ("החיה שלכם זקוקה לטיפול?", "אנחנו כאן בשבילה."),
    "מורה פרטית":          ("רוצים לשפר ציונים?", "בואו נתחיל."),
    "מורה פרטי":           ("רוצים לשפר ציונים?", "בואו נתחיל."),
    "מאמן כושר":           ("מוכנים לשנות הרגלים?", "בואו נתחיל."),
    "צילום":               ("יש לכם אירוע מיוחד?", "בואו נתעד אותו."),
    "אולם אירועים":        ("מתכננים אירוע?", "בואו לראות את האולם."),
    "פרחים":               ("צריכים פרחים?", "אנחנו כאן בשבילכם."),
    "סופרמרקט":            ("מתכננים קניות?", "בואו אלינו."),
    "חנות בגדים":          ("מחפשים סטייל חדש?", "קפצו לבקר."),
    "סטודיו":              ("יש לכם רעיון?", "בואו נבנה אותו יחד."),
    "אופטיקה":             ("צריכים משקפיים חדשים?", "קפצו לבדיקה."),
}
DEFAULT_FINAL_CTA = ("רוצים לדעת עוד?", "דברו איתנו.")


def _final_cta_for(category: str | None) -> tuple[str, str]:
    if category:
        for key, val in CATEGORY_FINAL_CTA.items():
            if key in category:
                return val
    return DEFAULT_FINAL_CTA


# Real testimonials (no fake WhatsApp mockups, no phone icons)
TESTIMONIALS = [
    ("דנה כ.", "שירות מעולה ומקצועי, התרשמתי מאוד מהיחס האישי. ממליצה בחום!"),
    ("מאיה ל.", "חוויה מדהימה — בהחלט אחזור. תמורה אמיתית למחיר ויחס מסור."),
    ("שירה ר.", "יחס אישי וחם, מחירים הוגנים. הופתעתי לטובה — שווה כל שקל."),
]

CITY_HE: dict[str, str] = {
    "jerusalem": "ירושלים",
    "tel aviv": "תל אביב", "tel-aviv": "תל אביב", "tel aviv-yafo": "תל אביב",
    "petah tikva": "פתח תקווה", "petach tikva": "פתח תקווה", "petah-tikva": "פתח תקווה",
    "haifa": "חיפה",
    "rishon": "ראשון לציון", "rishon lezion": "ראשון לציון",
    "rishon le zion": "ראשון לציון", "rishon-lezion": "ראשון לציון",
    "ramat gan": "רמת גן", "ramat-gan": "רמת גן",
    "bnei brak": "בני ברק", "holon": "חולון", "bat yam": "בת ים",
    "ashdod": "אשדוד", "netanya": "נתניה", "ashkelon": "אשקלון",
    "beer sheva": "באר שבע", "rehovot": "רחובות", "herzliya": "הרצליה",
    "kfar saba": "כפר סבא", "raanana": "רעננה", "modiin": "מודיעין",
    "lod": "לוד", "ramla": "רמלה",
}

DAY_HE = {
    "sunday": "ראשון", "monday": "שני", "tuesday": "שלישי",
    "wednesday": "רביעי", "thursday": "חמישי", "friday": "שישי",
    "saturday": "שבת",
}

HEBREW_RE = re.compile(r"[֐-׿]")


# ── Helpers ────────────────────────────────────────────────────────────
class Lead(NamedTuple):
    id: int
    name: str
    phone: str
    category: str | None
    city: str | None
    owner_name: str | None
    google_rating: float | None
    google_reviews: int | None
    services: str | None      # JSON array
    opening_hours: str | None  # JSON object


def _has_hebrew(s: str | None) -> bool:
    return bool(s) and bool(HEBREW_RE.search(s))


def _city_he(city: str | None) -> str:
    if not city or not city.strip():
        return ""
    key = city.strip().lower()
    if key in CITY_HE:
        return CITY_HE[key]
    if _has_hebrew(city):
        return city.strip()
    return ""


def _style_for(category: str | None) -> tuple[str, str]:
    if category:
        for key, val in CATEGORY_STYLE.items():
            if key in category:
                return val
    return DEFAULT_STYLE


def _image_for(category: str | None) -> str:
    if category:
        for key, val in CATEGORY_IMAGE_ID.items():
            if key in category:
                return val
    return DEFAULT_IMAGE_ID


def _services_for(category: str | None) -> list[tuple[str, str, str]]:
    if category:
        for key, val in CATEGORY_SERVICES.items():
            if key in category:
                return val
    return DEFAULT_SERVICES


def _services_from_db(raw: str | None, fallback: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """If DB has its own services list (JSON array of strings), use them with rotating
    icons + descriptions inferred from the fallback. Else return the fallback."""
    if not raw:
        return fallback
    try:
        items = json.loads(raw)
    except Exception:
        return fallback
    if not isinstance(items, list) or not items:
        return fallback
    out: list[tuple[str, str, str]] = []
    for i, name in enumerate(items[:3]):
        if not isinstance(name, str) or not name.strip():
            continue
        icon = (fallback[i] if i < len(fallback) else (SERVICE_ICON_POOL[i % len(SERVICE_ICON_POOL)], "", ""))[0]
        # Use fallback description if available, else generic
        desc = (fallback[i][2] if i < len(fallback) else "מענה מקצועי ואיכותי לכל פנייה.")
        out.append((icon, name.strip(), desc))
    return out or fallback


def _hours_from_db(raw: str | None) -> list[tuple[str, str]]:
    """Returns ordered (day_he, hours_str) pairs in Sun→Sat order, or [] if missing."""
    if not raw:
        return []
    try:
        h = json.loads(raw)
    except Exception:
        return []
    if not isinstance(h, dict):
        return []
    order = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    out = []
    for d in order:
        v = h.get(d)
        if isinstance(v, str):
            out.append((DAY_HE[d], _format_hours_string(v)))
    return out


def _parse_time_token(t: str) -> str:
    """Convert tokens like '9:30 am', '8 pm', '12', '4:30am' to 24h '09:30'."""
    t = t.strip().lower()
    is_am = "am" in t
    is_pm = "pm" in t
    t = re.sub(r"\s*(am|pm)\s*", "", t).strip()
    if not t:
        return ""
    m = re.match(r"(\d{1,2})(?::(\d{2}))?", t)
    if not m:
        return t
    hour = int(m.group(1))
    minute = m.group(2) or "00"
    if is_pm and hour < 12:
        hour += 12
    if is_am and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute}"


def _format_hours_string(raw: str) -> str:
    """Convert a Google-style hours string to clean Hebrew-friendly text."""
    if not raw:
        return ""
    # Strip narrow / non-breaking spaces that Google injects
    t = re.sub(r"[   ]", " ", raw).strip()
    low = t.lower()
    if "closed" in low or "סגור" in t:
        return "סגור"
    if "open 24" in low or "24 hours" in low or "24/7" in low:
        return "24 שעות"
    # Range like "9:30 am – 8 pm"
    m = re.match(r"(.+?)\s*[–\-—]\s*(.+)", t)
    if m:
        a = _parse_time_token(m.group(1))
        b = _parse_time_token(m.group(2))
        if a and b:
            return f"{a}–{b}"
    return re.sub(r"\s*(am|pm)\s*", "", t, flags=re.IGNORECASE).strip()


def _wa_number(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("0"):
        digits = "972" + digits[1:]
    return digits


def _slug(name: str, lead_id: int) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return f"{s}-{lead_id}" if s else str(lead_id)


def _strip_credentials(name: str) -> str:
    """Drop trailing parenthetical for cleaner display in the hero/nav."""
    return re.sub(r"\s*\([^)]+\)\s*$", "", name).strip()


# ── HTML template ──────────────────────────────────────────────────────
PAGE_TPL = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex,nofollow,noarchive">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://images.unsplash.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">

<style>
:root {{
  --bg: #0A0A0B;
  --surface: #131316;
  --surface-2: #17171B;
  --border: #1F1F23;
  --border-2: #2A2A30;
  --text: #F4F4F5;
  --text-2: #A1A1AA;
  --text-3: #6B6B72;
  --accent: {accent};
  --accent-dim: {accent}1f;
  --accent-glow: {accent}33;
  --display: "Heebo", "Inter", ui-sans-serif, system-ui, sans-serif;
  --body: "Inter", "Heebo", ui-sans-serif, system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, monospace;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
html, body {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--body);
  font-size: 17px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}
::selection {{ background: var(--accent); color: #0A0A0B; }}
a {{ color: inherit; text-decoration: none; }}
button {{ font: inherit; color: inherit; background: none; border: 0; cursor: pointer; }}

.mono {{ font-family: var(--mono); }}
.display {{ font-family: var(--display); letter-spacing: -0.025em; font-weight: 800; }}
.muted {{ color: var(--text-2); }}
.dim {{ color: var(--text-3); }}
.accent {{ color: var(--accent); }}
.container {{ max-width: 1320px; margin: 0 auto; padding: 0 32px; }}

/* nav */
.nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 50;
  padding: 18px 32px;
  backdrop-filter: blur(14px);
  background: rgba(10,10,11,0.7);
  border-bottom: 1px solid rgba(31,31,35,0.5);
}}
.nav-inner {{
  width: 100%; max-width: 1320px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
}}
.brand {{ display: flex; align-items: center; gap: 10px; font-family: var(--display); font-weight: 700; letter-spacing: -0.02em; font-size: 17px; max-width: 70%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.brand-mark {{
  width: 28px; height: 28px;
  display: grid; place-items: center;
  background: var(--accent); color: #fff;
  border-radius: 6px;
  flex-shrink: 0;
}}
.brand-mark .icon {{ width: 16px; height: 16px; }}
.icon {{ width: 1em; height: 1em; vertical-align: -0.125em; flex-shrink: 0; }}
.icon-md {{ width: 22px; height: 22px; }}
.icon-lg {{ width: 28px; height: 28px; }}
.nav-links {{ display: flex; align-items: center; gap: 28px; font-size: 14px; color: var(--text-2); }}
.nav-links a {{ transition: color 120ms ease; }}
.nav-links a:hover {{ color: var(--text); }}
.nav-cta {{
  padding: 8px 16px;
  background: var(--accent); color: #0A0A0B !important;
  border-radius: 8px;
  font-weight: 600;
  display: inline-flex; align-items: center; gap: 8px;
}}
.nav-cta:hover {{ filter: brightness(1.1); }}
.nav-cta svg {{ width: 14px; height: 14px; }}
@media (max-width: 767px) {{ .nav-links a:not(.nav-cta) {{ display: none; }} }}

/* hero */
.hero {{
  position: relative;
  min-height: 78vh;
  padding: 160px 0 100px;
  overflow: hidden;
  isolation: isolate;
}}
.hero-bg {{
  position: absolute; inset: 0;
  background-image:
    linear-gradient(180deg, rgba(10,10,11,0.55) 0%, rgba(10,10,11,0.7) 50%, var(--bg) 100%),
    linear-gradient(270deg, rgba(10,10,11,0.5) 0%, rgba(10,10,11,0.85) 100%),
    url('https://images.unsplash.com/{image_id}?w=1800&auto=format&fit=crop&q=80');
  background-size: cover;
  background-position: center;
  z-index: -2;
  opacity: 0.85;
}}
.hero-grain {{
  position: absolute; inset: 0; z-index: -1;
  background-image: radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 3px 3px;
  mix-blend-mode: overlay;
  pointer-events: none;
}}
.hero-glow {{
  position: absolute; top: 50%; left: -10%;
  width: 600px; height: 600px;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 60%);
  filter: blur(80px);
  z-index: -1;
  pointer-events: none;
}}
.icon-inline-row {{ display: inline-flex; align-items: center; gap: 6px; }}
.icon-inline-row .icon {{ width: 14px; height: 14px; color: var(--accent); }}
.hero-eyebrow {{
  display: inline-flex; align-items: center; gap: 10px;
  padding: 6px 14px;
  border: 1px solid var(--border-2);
  border-radius: 999px;
  background: rgba(19,19,22,0.7);
  backdrop-filter: blur(8px);
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text-2);
  margin-bottom: 32px;
}}
.hero-eyebrow .dot {{
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-dim);
  animation: pulse 2.4s ease-in-out infinite;
}}
@keyframes pulse {{
  0%,100% {{ box-shadow: 0 0 0 4px var(--accent-dim); }}
  50%     {{ box-shadow: 0 0 0 7px {accent}0d; }}
}}
.hero h1 {{
  font-family: var(--display);
  font-weight: 900;
  font-size: clamp(44px, 7vw, 96px);
  line-height: 1;
  letter-spacing: -0.04em;
  max-width: 18ch;
  margin-bottom: 24px;
}}
.hero h1 .accent {{ color: var(--accent); }}
.hero-sub {{
  font-size: clamp(16px, 1.2vw, 19px);
  color: var(--text-2);
  max-width: 56ch;
  margin-bottom: 36px;
  line-height: 1.55;
}}

.cta-row {{ display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
.btn {{
  display: inline-flex; align-items: center; gap: 10px;
  padding: 14px 22px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  font-family: var(--display);
  letter-spacing: -0.005em;
  transition: all 160ms ease;
  border: 1px solid transparent;
}}
.btn-primary {{
  background: var(--accent); color: #0A0A0B;
  box-shadow: 0 0 0 1px {accent}66, 0 12px 30px -12px var(--accent-glow);
}}
.btn-primary:hover {{ filter: brightness(1.08); transform: translateY(-1px); }}
.btn-ghost {{
  color: var(--text);
  border: 1px solid var(--border-2);
  background: rgba(19,19,22,0.6);
  backdrop-filter: blur(6px);
}}
.btn-ghost:hover {{ border-color: #3f3f48; background: rgba(23,23,27,0.85); }}
.btn svg {{ width: 18px; height: 18px; }}

/* hero meta strip */
.hero-meta {{
  margin-top: 64px;
  padding-top: 28px;
  border-top: 1px solid var(--border);
  display: flex; justify-content: flex-start; gap: 56px; flex-wrap: wrap;
  font-family: var(--mono); font-size: 11px;
  color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.08em;
}}
.hero-meta-block {{ display: flex; flex-direction: column; gap: 6px; }}
.hero-meta-block strong {{ color: var(--text); font-weight: 600; letter-spacing: -0.01em; font-size: 18px; font-family: var(--display); text-transform: none; }}

/* sections */
section {{ position: relative; }}
.section {{ padding: 120px 0; border-top: 1px solid var(--border); }}
.section-tag {{
  display: inline-flex; align-items: center; gap: 10px;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.12em;
  margin-bottom: 24px;
}}
.section-tag::before {{
  content: ""; display: block; width: 24px; height: 1px; background: var(--accent);
}}
.section h2 {{
  font-family: var(--display);
  font-weight: 900;
  font-size: clamp(36px, 4.5vw, 64px);
  line-height: 1;
  letter-spacing: -0.035em;
  max-width: 22ch;
  margin-bottom: 14px;
}}
.section h2 .accent {{ color: var(--accent); }}
.section .section-lead {{ color: var(--text-2); font-size: 17px; max-width: 60ch; }}

/* problem list — bold numbered statements */
.problem-list {{ display: flex; flex-direction: column; margin-top: 40px; }}
.problem-item {{
  font-family: var(--display); font-weight: 800;
  font-size: clamp(28px, 4vw, 56px);
  line-height: 1.05;
  letter-spacing: -0.035em;
  padding: 28px 0;
  border-top: 1px solid var(--border);
  display: flex; align-items: baseline; gap: 28px;
  color: var(--text);
}}
.problem-item:last-child {{ border-bottom: 1px solid var(--border); }}
.problem-num {{
  font-family: var(--mono); font-size: 13px; font-weight: 400;
  color: var(--text-3); letter-spacing: 0.04em;
  flex-shrink: 0; min-width: 32px;
}}
.problem-item .strike {{ color: var(--text-3); }}

/* features (services) */
.features {{ display: flex; flex-direction: column; gap: 0; margin-top: 40px; }}
.feature {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
  padding: 60px 0;
  border-top: 1px solid var(--border);
}}
.feature:first-child {{ border-top: 0; padding-top: 0; }}
.feature.reverse .feature-text {{ order: 2; }}
.feature-num {{
  font-family: var(--mono); font-size: 13px;
  color: var(--accent); letter-spacing: 0.06em;
  margin-bottom: 14px;
}}
.feature-icon {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 56px; height: 56px;
  border-radius: 12px;
  background: var(--accent-dim);
  color: var(--accent);
  margin-bottom: 18px;
}}
.feature-icon .icon {{ width: 26px; height: 26px; stroke-width: 1.7; }}
.feature-art-icon .icon {{ width: 64px; height: 64px; opacity: 0.85; }}
.feature-title {{
  font-family: var(--display); font-weight: 800;
  font-size: clamp(28px, 3vw, 42px);
  line-height: 1.05;
  letter-spacing: -0.025em;
  margin-bottom: 16px;
}}
.feature-desc {{
  color: var(--text-2);
  font-size: 17px;
  max-width: 44ch;
}}
.feature-art {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 32px;
  min-height: 240px;
  display: flex; flex-direction: column; justify-content: space-between; gap: 20px;
  position: relative;
  overflow: hidden;
}}
.feature-art-icon {{ color: var(--accent); opacity: 0.55; }}
.feature-art-num {{
  font-family: var(--mono); font-size: 12px;
  color: var(--text-3); letter-spacing: 0.1em;
  text-transform: uppercase;
}}
.feature-art-title {{
  font-family: var(--display); font-weight: 700;
  font-size: 22px;
  letter-spacing: -0.02em;
}}
.feature-art-bar {{
  position: absolute; right: 0; top: 0; bottom: 0;
  width: 3px; background: var(--accent);
}}

/* bento — info tiles */
.bento {{
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  margin-top: 60px;
}}
.tile {{
  background: var(--surface);
  padding: 28px;
  display: flex; flex-direction: column; justify-content: space-between;
  gap: 14px;
  position: relative;
  min-height: 220px;
}}
.tile:hover {{ background: var(--surface-2); }}
.tile-tag {{
  font-family: var(--mono); font-size: 11px;
  color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.12em;
}}
.tile-title {{
  font-family: var(--display); font-weight: 700;
  font-size: 22px; line-height: 1.1; letter-spacing: -0.02em;
}}
.tile-big {{
  font-family: var(--display); font-weight: 800;
  font-size: clamp(36px, 4vw, 56px);
  line-height: 1; letter-spacing: -0.035em;
  color: var(--text);
}}
.tile-big .accent {{ color: var(--accent); }}
.tile-desc {{ color: var(--text-2); font-size: 14px; line-height: 1.5; }}
.tile-list {{ list-style: none; display: flex; flex-direction: column; gap: 8px; font-family: var(--mono); font-size: 12px; color: var(--text-2); }}
.tile-list li {{ display: flex; justify-content: space-between; align-items: center; }}
.tile-list .day {{ color: var(--text-3); }}
.tile-list .hours {{ color: var(--text); }}
.tile-w3 {{ grid-column: span 3; }}
.tile-w2 {{ grid-column: span 2; }}
.tile-w4 {{ grid-column: span 4; }}

/* testimonials */
.testi-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  margin-top: 60px;
}}
.testi {{
  background: var(--surface);
  padding: 36px 28px;
  display: flex; flex-direction: column; gap: 18px;
  min-height: 260px;
}}
.testi-stars {{ color: #f59e0b; font-size: 18px; letter-spacing: 2px; }}
.testi-quote {{ color: var(--text); font-size: 16px; line-height: 1.55; flex: 1; }}
.testi-foot {{
  display: flex; align-items: center; gap: 12px;
  padding-top: 16px; border-top: 1px solid var(--border);
}}
.testi-avatar {{
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--accent-dim); color: var(--accent);
  display: grid; place-items: center;
  font-family: var(--display); font-weight: 700;
  font-size: 16px;
}}
.testi-name {{ font-family: var(--display); font-weight: 700; font-size: 14px; color: var(--text); }}
.testi-source {{ font-family: var(--mono); font-size: 11px; color: var(--text-3); }}

/* contact */
.contact-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  margin-top: 40px;
}}
.contact-actions {{ display: flex; flex-direction: column; gap: 12px; }}
.contact-row {{
  display: flex; align-items: center; gap: 18px;
  padding: 20px 22px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  transition: border-color 160ms, background 160ms;
}}
.contact-row:hover {{ border-color: var(--accent); background: var(--surface-2); }}
.contact-row-icon {{
  width: 44px; height: 44px;
  border-radius: 10px;
  background: var(--accent-dim);
  color: var(--accent);
  display: grid; place-items: center;
}}
.contact-row-icon svg {{ width: 20px; height: 20px; }}
.contact-row-label {{ font-family: var(--mono); font-size: 11px; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.1em; }}
.contact-row-value {{ font-family: var(--display); font-weight: 700; font-size: 17px; color: var(--text); }}

.contact-form {{ display: flex; flex-direction: column; gap: 12px; }}
.contact-form input, .contact-form textarea {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  color: var(--text);
  font-family: var(--body);
  font-size: 15px;
  transition: border-color 160ms;
}}
.contact-form input:focus, .contact-form textarea:focus {{
  outline: none; border-color: var(--accent);
}}
.contact-form textarea {{ resize: none; min-height: 110px; }}
.contact-form button {{
  background: var(--accent); color: #0A0A0B;
  font-family: var(--display); font-weight: 700; font-size: 15px;
  padding: 16px; border-radius: 10px;
  cursor: pointer;
  transition: filter 160ms;
}}
.contact-form button:hover {{ filter: brightness(1.08); }}

/* final cta */
.final {{
  padding: 140px 0 130px;
  border-top: 1px solid var(--border);
  position: relative;
  overflow: hidden;
}}
.final h2 {{
  font-family: var(--display); font-weight: 900;
  font-size: clamp(40px, 6vw, 88px);
  line-height: 1;
  letter-spacing: -0.04em;
  max-width: 18ch;
  margin-bottom: 32px;
}}
.final h2 .accent {{ color: var(--accent); }}
.final-glow {{
  position: absolute;
  left: -10%; top: 50%;
  transform: translateY(-50%);
  width: 600px; height: 600px;
  background: radial-gradient(circle, var(--accent-glow) 0%, transparent 60%);
  filter: blur(80px);
  pointer-events: none;
}}

/* footer */
footer {{
  border-top: 1px solid var(--border);
  padding: 60px 0 30px;
}}
.footer-row {{
  display: flex; justify-content: space-between; align-items: center; gap: 24px; flex-wrap: wrap;
  font-family: var(--mono); font-size: 11px; color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.08em;
  padding-top: 20px; border-top: 1px solid var(--border);
}}

/* floating CTAs */
.cta-float {{
  position: fixed; bottom: 24px; right: 24px; z-index: 60;
  display: flex; flex-direction: column; gap: 12px;
}}
.cta-float a {{
  width: 56px; height: 56px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10px 30px -8px rgba(0,0,0,0.6);
  transition: transform .2s, filter .2s;
}}
.cta-float a:hover {{ transform: scale(1.08); }}
.cta-float .wa {{ background: #25D366; color: #fff; }}
.cta-float .ph {{ background: var(--accent); color: #0A0A0B; }}
.cta-float svg {{ width: 26px; height: 26px; }}

/* fade-in on scroll (no GSAP — pure CSS) */
.fadein {{ opacity: 0; transform: translateY(16px); transition: opacity 700ms ease, transform 700ms ease; }}
.fadein.in {{ opacity: 1; transform: none; }}

/* responsive */
@media (max-width: 1000px) {{
  .feature, .feature.reverse {{ grid-template-columns: 1fr; gap: 32px; }}
  .feature.reverse .feature-text {{ order: 0; }}
  .bento {{ grid-template-columns: repeat(2, 1fr); }}
  .tile-w3, .tile-w2, .tile-w4 {{ grid-column: span 2; }}
  .testi-grid {{ grid-template-columns: 1fr; }}
  .contact-grid {{ grid-template-columns: 1fr; gap: 32px; }}
  .section {{ padding: 80px 0; }}
}}
@media (max-width: 600px) {{
  .container {{ padding: 0 18px; }}
  .nav {{ padding: 14px 18px; }}
  .hero {{ padding: 130px 0 70px; }}
  .hero-meta {{ gap: 28px; }}
  .bento {{ grid-template-columns: 1fr; }}
  .tile-w3, .tile-w2, .tile-w4 {{ grid-column: span 1; }}
  .problem-item {{ font-size: clamp(22px, 6vw, 36px); gap: 18px; padding: 20px 0; }}
  .cta-row {{ flex-direction: column; align-items: stretch; }}
  .btn {{ justify-content: center; }}
}}
</style>
</head>
<body>

<nav class="nav">
  <div class="nav-inner">
    <div class="brand">
      <span class="brand-mark">{icon_svg_brand}</span>
      <span>{name_short}</span>
    </div>
    <div class="nav-links">
      <a href="#services">שירותים</a>
      <a href="#testimonials">המלצות</a>
      <a href="#about">עלינו</a>
      <a href="#contact">צרו קשר</a>
      <a href="https://wa.me/{wa}" class="nav-cta">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg>
        ווצאפ
      </a>
    </div>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-bg"></div>
  <div class="hero-grain"></div>
  <div class="hero-glow"></div>
  <div class="container">
    <div class="hero-eyebrow">
      <span class="dot"></span>
      <span class="icon-inline-row">{icon_svg_eyebrow}<span>{category_label}{location_inline}</span></span>
    </div>
    <h1>{name_short}<br><span class="accent">{tagline}</span></h1>
    <p class="hero-sub">{hero_p}</p>
    <div class="cta-row">
      <a href="https://wa.me/{wa}" class="btn btn-primary">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg>
        שלחו הודעה
      </a>
      <a href="tel:{phone}" class="btn btn-ghost">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 15.5c-1.2 0-2.5-.2-3.6-.6a1 1 0 0 0-1 .2l-2.2 2.2a15 15 0 0 1-6.6-6.6l2.2-2.2a1 1 0 0 0 .2-1A11.4 11.4 0 0 1 8.5 4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1A17 17 0 0 0 20 21a1 1 0 0 0 1-1v-3.5a1 1 0 0 0-1-1Z"/></svg>
        {phone}
      </a>
    </div>
    <div class="hero-meta">
      <div class="hero-meta-block"><span>דירוג גוגל</span><strong>{rating_str}</strong></div>
      <div class="hero-meta-block"><span>ביקורות</span><strong>{reviews_str}</strong></div>
      <div class="hero-meta-block"><span>תחום</span><strong>{category_label}</strong></div>
    </div>
  </div>
</section>

<!-- SERVICES (FEATURES) -->
<section id="services" class="section">
  <div class="container">
    <div class="section-tag">השירותים שלנו</div>
    <h2>למה לבחור<br><span class="accent">ב-{name_short}</span></h2>
    <div class="features">
      {features_html}
    </div>
  </div>
</section>

<!-- BENTO — info tiles -->
<section id="about" class="section">
  <div class="container">
    <div class="section-tag">מי אנחנו</div>
    <h2>מקצועיות.<br><span class="accent">תוצאות. שירות.</span></h2>
    <div class="bento">
      {bento_html}
    </div>
  </div>
</section>

<!-- TESTIMONIALS -->
<section id="testimonials" class="section">
  <div class="container">
    <div class="section-tag">לקוחות שלנו</div>
    <h2>מה אומרים<br><span class="accent">עלינו</span></h2>
    <div class="testi-grid">
      {testimonials_html}
    </div>
  </div>
</section>

<!-- CONTACT -->
<section id="contact" class="section">
  <div class="container">
    <div class="section-tag">צרו קשר</div>
    <h2>דברו איתנו<br><span class="accent">עכשיו</span></h2>
    <p class="section-lead">נחזור אליכם תוך זמן קצר. ללא התחייבות.</p>
    <div class="contact-grid">
      <div class="contact-actions">
        <a href="tel:{phone}" class="contact-row">
          <div class="contact-row-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 15.5c-1.2 0-2.5-.2-3.6-.6a1 1 0 0 0-1 .2l-2.2 2.2a15 15 0 0 1-6.6-6.6l2.2-2.2a1 1 0 0 0 .2-1A11.4 11.4 0 0 1 8.5 4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1A17 17 0 0 0 20 21a1 1 0 0 0 1-1v-3.5a1 1 0 0 0-1-1Z"/></svg></div>
          <div><div class="contact-row-label">התקשרו</div><div class="contact-row-value">{phone}</div></div>
        </a>
        <a href="https://wa.me/{wa}" class="contact-row">
          <div class="contact-row-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg></div>
          <div><div class="contact-row-label">ווצאפ</div><div class="contact-row-value">שלחו הודעה</div></div>
        </a>
        {location_row}
      </div>
      <form class="contact-form" onsubmit="handleSubmit(event)">
        <input type="text" placeholder="שם מלא" required>
        <input type="tel" placeholder="מספר טלפון" required>
        <input type="email" placeholder="אימייל (אופציונלי)">
        <textarea placeholder="איך נוכל לעזור?"></textarea>
        <button type="submit">שלחו פנייה</button>
      </form>
    </div>
  </div>
</section>

<!-- FINAL CTA -->
<section class="final">
  <div class="final-glow"></div>
  <div class="container">
    <h2>{cta_q}<br><span class="accent">{cta_a}</span></h2>
    <div class="cta-row">
      <a href="https://wa.me/{wa}" class="btn btn-primary">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg>
        שלחו הודעה עכשיו
      </a>
      <a href="tel:{phone}" class="btn btn-ghost">
        התקשרו ישירות
      </a>
    </div>
  </div>
</section>

<footer>
  <div class="container">
    <div class="footer-row">
      <span>© {year} {name} · כל הזכויות שמורות</span>
      <span>{phone}{footer_loc}</span>
    </div>
  </div>
</footer>

<div class="cta-float">
  <a href="https://wa.me/{wa}" class="wa" aria-label="WhatsApp">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413z"/></svg>
  </a>
  <a href="tel:{phone}" class="ph" aria-label="Call">
    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 15.5c-1.2 0-2.5-.2-3.6-.6a1 1 0 0 0-1 .2l-2.2 2.2a15 15 0 0 1-6.6-6.6l2.2-2.2a1 1 0 0 0 .2-1A11.4 11.4 0 0 1 8.5 4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1A17 17 0 0 0 20 21a1 1 0 0 0 1-1v-3.5a1 1 0 0 0-1-1Z"/></svg>
  </a>
</div>

<script>
// fade-in on scroll — uses IntersectionObserver, no library
(function () {{
  document.querySelectorAll('.section, .feature, .tile, .testi, .problem-item').forEach(el => el.classList.add('fadein'));
  const io = new IntersectionObserver((entries) => {{
    entries.forEach(e => {{ if (e.isIntersecting) {{ e.target.classList.add('in'); io.unobserve(e.target); }} }});
  }}, {{ threshold: 0.12 }});
  document.querySelectorAll('.fadein').forEach(el => io.observe(el));
}})();
function handleSubmit(e) {{
  e.preventDefault();
  e.target.innerHTML = '<div style="text-align:center;padding:40px 20px;color:#6dd28a;font-family:var(--display);font-weight:700;font-size:18px;">✓ הפנייה נשלחה — נחזור אליכם בהקדם</div>';
}}
</script>
</body>
</html>
"""


def render_page(lead: Lead) -> str:
    accent, icon_key = _style_for(lead.category)
    image_id = _image_for(lead.category)
    fallback_services = _services_for(lead.category)
    services = _services_from_db(lead.services, fallback_services)
    hours = _hours_from_db(lead.opening_hours)
    city = _city_he(lead.city)
    category_label = (lead.category or "השירות שלנו").strip()
    cta_q, cta_a = _final_cta_for(lead.category)

    name_short = _strip_credentials(lead.name)
    rating_str = f"{lead.google_rating:.1f}★" if lead.google_rating else "—"
    reviews_str = f"{lead.google_reviews}+" if lead.google_reviews else "—"
    location_inline = f" · ב{city}" if city else ""
    footer_loc = f" · {city}" if city else ""

    # Features (services) — alternating layout
    features_html = ""
    for i, (sicon_key, stitle, sdesc) in enumerate(services):
        reverse = " reverse" if i % 2 == 1 else ""
        sicon_svg = svg_icon(sicon_key)
        features_html += f"""
        <div class="feature{reverse}">
          <div class="feature-text">
            <div class="feature-num">0{i+1} / {len(services)}</div>
            <div class="feature-icon">{sicon_svg}</div>
            <div class="feature-title">{html.escape(stitle)}</div>
            <p class="feature-desc">{html.escape(sdesc)}</p>
          </div>
          <div class="feature-art">
            <div class="feature-art-bar"></div>
            <div class="feature-art-icon">{sicon_svg}</div>
            <div>
              <div class="feature-art-num">שירות {i+1:02d}</div>
              <div class="feature-art-title">{html.escape(stitle)}</div>
            </div>
          </div>
        </div>
        """

    # Bento tiles — flexible content based on what's known
    bento_blocks: list[str] = []

    # Tile: rating (large)
    if lead.google_rating:
        rounded = f"{lead.google_rating:.1f}"
        revs = f"{lead.google_reviews}+ ביקורות" if lead.google_reviews else ""
        bento_blocks.append(f"""
        <div class="tile tile-w3">
          <div class="tile-tag">דירוג גוגל</div>
          <div class="tile-big"><span class="accent">{rounded}★</span></div>
          <div class="tile-desc">{revs} שמדברות בעד עצמן.</div>
        </div>""")
    else:
        bento_blocks.append(f"""
        <div class="tile tile-w3">
          <div class="tile-tag">המומחיות שלנו</div>
          <div class="tile-big"><span class="accent">{html.escape(category_label)}</span></div>
          <div class="tile-desc">תחום עיסוק עיקרי, בליווי שנים של ניסיון.</div>
        </div>""")

    # Tile: location
    if city:
        bento_blocks.append(f"""
        <div class="tile tile-w3">
          <div class="tile-tag">איפה אנחנו</div>
          <div class="tile-big">{html.escape(city)}</div>
          <div class="tile-desc">פעילים ב{html.escape(city)} והסביבה.</div>
        </div>""")
    else:
        bento_blocks.append(f"""
        <div class="tile tile-w3">
          <div class="tile-tag">איפה אנחנו</div>
          <div class="tile-big">ברחבי הארץ</div>
          <div class="tile-desc">מגיעים אליכם — או שתבואו אלינו.</div>
        </div>""")

    # Tile: opening hours (if available)
    if hours:
        rows = "".join(
            f'<li><span class="day">{html.escape(d)}</span><span class="hours">{html.escape(h)}</span></li>'
            for d, h in hours
        )
        bento_blocks.append(f"""
        <div class="tile tile-w2">
          <div class="tile-tag">שעות פעילות</div>
          <ul class="tile-list">{rows}</ul>
        </div>""")
    else:
        bento_blocks.append(f"""
        <div class="tile tile-w2">
          <div class="tile-tag">שעות פעילות</div>
          <div class="tile-title">א'-ה': 09:00–19:00</div>
          <div class="tile-desc">ו': 09:00–13:00 · שבת: סגור</div>
        </div>""")

    # Tile: phone
    bento_blocks.append(f"""
    <div class="tile tile-w2">
      <div class="tile-tag">התקשרו</div>
      <div class="tile-title">{html.escape(lead.phone)}</div>
      <div class="tile-desc">זמינים בכל יום עבודה.</div>
    </div>""")

    # Tile: trust statement (full width)
    bento_blocks.append(f"""
    <div class="tile tile-w2">
      <div class="tile-tag">העדויות</div>
      <div class="tile-title">לקוחות חוזרים שוב ושוב</div>
      <div class="tile-desc">שירות אישי, מחיר הוגן, תוצאות שמדברות בעד עצמן.</div>
    </div>""")

    bento_html = "\n".join(bento_blocks)

    # Testimonials
    testimonials_html = "".join(
        f"""
        <div class="testi">
          <div class="testi-stars">★★★★★</div>
          <p class="testi-quote">{html.escape(t[1])}</p>
          <div class="testi-foot">
            <div class="testi-avatar">{html.escape(t[0][0])}</div>
            <div>
              <div class="testi-name">{html.escape(t[0])}</div>
              <div class="testi-source">לקוח/ה ב-Google</div>
            </div>
          </div>
        </div>"""
        for t in TESTIMONIALS[:3]
    )

    # Location row in contact section
    if city:
        location_row = f"""
        <div class="contact-row">
          <div class="contact-row-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a8 8 0 0 0-8 8c0 5.4 7 11.4 7.3 11.7.4.4 1 .4 1.4 0 .3-.3 7.3-6.3 7.3-11.7a8 8 0 0 0-8-8Zm0 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6Z"/></svg></div>
          <div><div class="contact-row-label">מיקום</div><div class="contact-row-value">{html.escape(city)}</div></div>
        </div>"""
    else:
        location_row = ""

    name_safe = html.escape(lead.name)
    name_short_safe = html.escape(name_short)
    tagline = html.escape(city or "ישראל")

    return PAGE_TPL.format(
        title=f"{name_safe} — {html.escape(category_label)}{(' ב' + html.escape(city)) if city else ''}",
        desc=f"{name_safe} — {html.escape(category_label)} מקצועי{(' ב' + html.escape(city)) if city else ''}. שירות אישי, ניסיון של שנים, מחיר הוגן.",
        accent=accent,
        icon_svg_brand=svg_icon(icon_key),
        icon_svg_eyebrow=svg_icon(icon_key),
        image_id=image_id,
        name=name_safe,
        name_short=name_short_safe,
        category_label=html.escape(category_label),
        location_inline=location_inline,
        tagline=tagline,
        hero_p="שירות מקצועי, אמין ובמחיר הוגן. מהפנייה הראשונה ועד התוצאה — אנחנו כאן בשבילכם.",
        rating_str=rating_str,
        reviews_str=reviews_str,
        features_html=features_html,
        bento_html=bento_html,
        testimonials_html=testimonials_html,
        location_row=location_row,
        wa=_wa_number(lead.phone),
        phone=html.escape(lead.phone),
        footer_loc=html.escape(footer_loc),
        year="2026",
        cta_q=html.escape(cta_q),
        cta_a=html.escape(cta_a),
    )


# ── Loading + writing ─────────────────────────────────────────────────
def load_leads(db_path: Path) -> list[Lead]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT id, name, phone, category, city, owner_name,
               google_rating, google_reviews, services, opening_hours
        FROM businesses
        WHERE ((website IS NULL OR website='') OR (quality_score < 8))
          AND phone IS NOT NULL AND phone!=''
          AND (blacklisted IS NULL OR blacklisted=0)
        ORDER BY COALESCE(lead_score,0) DESC, id ASC
    """).fetchall()
    con.close()
    return [Lead(**dict(r)) for r in rows]


def write_site(leads: list[Lead], out: Path, base_url: str) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    (out / "l").mkdir(exist_ok=True)
    (out / "index.html").write_text(
        "<!DOCTYPE html><html lang=he dir=rtl><meta charset=utf-8>"
        "<title>Leads landing pages</title>"
        "<body style='font-family:system-ui;padding:40px;color:#475569;background:#0A0A0B'>"
        "<p style='color:#A1A1AA'>Per-lead landing pages.</p>",
        encoding="utf-8",
    )
    (out / "_redirects").write_text("/l/* /l/:splat/index.html 200\n", encoding="utf-8")

    manifest_rows: list[dict] = []
    skipped_no_he = 0
    for lead in leads:
        if not _has_hebrew(lead.name):
            skipped_no_he += 1
            continue
        slug = _slug(lead.name, lead.id)
        page_dir = out / "l" / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_page(lead), encoding="utf-8")
        url_path = f"/l/{slug}/"
        full_url = f"{base_url.rstrip('/')}{url_path}?utm_source=wa&utm_lead={lead.id}"
        manifest_rows.append({
            "id": lead.id, "name": lead.name, "phone": lead.phone,
            "category": lead.category or "",
            "city": _city_he(lead.city) or (lead.city or ""),
            "url_path": url_path, "full_url": full_url,
        })

    with (out / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id","name","phone","category","city","url_path","full_url"])
        w.writeheader()
        w.writerows(manifest_rows)

    print(f"Generated {len(manifest_rows)} pages -> {out}")
    if skipped_no_he:
        print(f"Skipped {skipped_no_he} leads with non-Hebrew business names.")
    return manifest_rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="e:/system/leads.db")
    ap.add_argument("--out", default="e:/system/leads-landing-pages")
    ap.add_argument("--base-url", default="https://leads-landing-pages.pages.dev")
    args = ap.parse_args()

    leads = load_leads(Path(args.db))
    if not leads:
        print("No leads found.", file=sys.stderr)
        sys.exit(1)
    write_site(leads, Path(args.out), args.base_url)


if __name__ == "__main__":
    main()
