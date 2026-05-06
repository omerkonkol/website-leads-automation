const CITY_HE: Record<string, string> = {
  "jerusalem": "ירושלים",
  "tel aviv": "תל אביב",
  "tel-aviv": "תל אביב",
  "tel aviv-yafo": "תל אביב",
  "petah tikva": "פתח תקווה",
  "petach tikva": "פתח תקווה",
  "petah-tikva": "פתח תקווה",
  "haifa": "חיפה",
  "rishon": "ראשון לציון",
  "rishon lezion": "ראשון לציון",
  "rishon le zion": "ראשון לציון",
  "rishon-lezion": "ראשון לציון",
  "ramat gan": "רמת גן",
  "ramat-gan": "רמת גן",
  "bnei brak": "בני ברק",
  "holon": "חולון",
  "bat yam": "בת ים",
  "ashdod": "אשדוד",
  "netanya": "נתניה",
  "ashkelon": "אשקלון",
  "beer sheva": "באר שבע",
  "be'er sheva": "באר שבע",
  "rehovot": "רחובות",
  "herzliya": "הרצליה",
  "kfar saba": "כפר סבא",
  "kfar-saba": "כפר סבא",
  "raanana": "רעננה",
  "modi'in": "מודיעין",
  "modiin": "מודיעין",
  "lod": "לוד",
  "ramla": "רמלה",
  "rahat": "רהט",
  "nazareth": "נצרת",
  "tiberias": "טבריה",
  "eilat": "אילת",
  "kiryat ata": "קריית אתא",
  "kiryat gat": "קריית גת",
  "kiryat motzkin": "קריית מוצקין",
  "kiryat ono": "קריית אונו",
  "kiryat yam": "קריית ים",
  "kiryat bialik": "קריית ביאליק",
  "givatayim": "גבעתיים",
  "hadera": "חדרה",
  "ness ziona": "נס ציונה",
  "yehud": "יהוד",
  "or yehuda": "אור יהודה",
  "rosh haayin": "ראש העין",
  "rosh ha'ayin": "ראש העין",
  "or akiva": "אור עקיבא",
  "afula": "עפולה",
  "akko": "עכו",
  "acre": "עכו",
  "karmiel": "כרמיאל",
  "nahariya": "נהריה",
  "tzfat": "צפת",
  "safed": "צפת",
};

const HEBREW_RE = /[֐-׿]/;

function hasHebrew(s: string | null | undefined): boolean {
  return !!s && HEBREW_RE.test(s);
}

export function isFullyHebrewSafe(lead: LeadForMessage): boolean {
  // Business name MUST contain Hebrew (per user rule: everything in Hebrew except NovaDigital)
  return hasHebrew(lead.name);
}

/**
 * Returns the city as a Hebrew "ב{city}" phrase, or "באזורכם" fallback.
 * Always Hebrew — never English (per user rule).
 */
function cityPhrase(city: string | null | undefined): string {
  if (!city || !city.trim()) return "באזורכם";
  const key = city.trim().toLowerCase();
  if (CITY_HE[key]) return "ב" + CITY_HE[key];
  if (hasHebrew(city)) return "ב" + city.trim();
  return "באזורכם";
}

export interface LeadForMessage {
  id: number;
  name: string;
  phone: string;
  category: string | null;
  city: string | null;
  owner_name: string | null;
  google_rating?: number | null;
  google_reviews?: number | null;
}

// ── Personalization helpers ───────────────────────────────────────────

/**
 * Maps category → the Hebrew word for "the workplace" used in
 * "אין ל{workplace} אתר רשמי".
 */
function workplaceWord(category: string | null | undefined): string {
  const c = (category || "").trim();
  if (!c) return "לעסק";
  if (/עורך דין|משרד עורכי דין|נוטריון/.test(c)) return "למשרד";
  if (/רואה חשבון|רו"ח/.test(c)) return "למשרד";
  if (/מרפאה|מרפאת|רופא|וטרינר|קליניקה/.test(c)) return "למרפאה";
  if (/מסעדה|פיצ|בית קפה|פאב|בר|דיינר/.test(c)) return "למסעדה";
  if (/מספרה|ברבר|סלון/.test(c)) return "לסלון";
  if (/חנות|שוק|בוטיק/.test(c)) return "לחנות";
  if (/אולם/.test(c)) return "לאולם";
  if (/מוסך|גרז'/.test(c)) return "למוסך";
  if (/סטודיו/.test(c)) return "לסטודיו";
  if (/בית ספר|מוסד|אקדמיה/.test(c)) return "למוסד";
  return "לעסק";
}

/**
 * Strips parenthetical credentials like "(LLM, Harvard)" from a name.
 * Returns { trimmedName, credentials | null }.
 */
function splitCredentials(name: string): { trimmedName: string; credentials: string | null } {
  const m = name.match(/^(.*?)\s*\(([^)]+)\)\s*$/);
  if (m) {
    return { trimmedName: m[1].trim().replace(/[,，]\s*$/, ""), credentials: m[2].trim() };
  }
  return { trimmedName: name.trim(), credentials: null };
}

/** Translates common English credentials inside parentheses to Hebrew. */
function translateCredentials(creds: string): string {
  return creds
    .replace(/\bHarvard\b/gi, "הרווארד")
    .replace(/\bMIT\b/gi, "MIT")
    .replace(/\bOxford\b/gi, "אוקספורד")
    .replace(/\bCambridge\b/gi, "קיימברידג'")
    .replace(/\bStanford\b/gi, "סטנפורד")
    .replace(/\bYale\b/gi, "ייל");
}

/**
 * Returns a Hebrew "we saw your impressive Google rating (...)" opener
 * when the lead has a strong, well-reviewed Google rating; otherwise null.
 */
function ratingOpener(
  rating: number | null | undefined,
  count: number | null | undefined
): string | null {
  if (!rating || !count) return null;
  if (rating < 4.5 || count < 10) return null;
  const rounded = Number.isInteger(rating) ? rating.toFixed(1) : rating.toFixed(1);
  return `ראינו את הדירוג המרשים שלכם בגוגל (${rounded}★ עם ${count}+ ביקורות)`;
}

export function buildLeadMessage(lead: LeadForMessage, url: string): string {
  const workplace = workplaceWord(lead.category);
  const { trimmedName, credentials } = splitCredentials(lead.name);
  const credentialsHe = credentials ? translateCredentials(credentials) : null;
  const ratingLine = ratingOpener(lead.google_rating, lead.google_reviews);

  // Build the first sentence based on what we actually know:
  //  1. Has parenthetical credentials  → reference them
  //  2. Else has strong Google rating  → reference it
  //  3. Else                           → open directly, no flattery
  let firstSentence: string;
  if (credentialsHe) {
    firstSentence = `שלום, ${trimmedName}. נחשפנו לרקע המקצועי המרשים שלכם (${credentialsHe}) ושמנו לב שאין ${workplace} אתר רשמי.`;
  } else if (ratingLine) {
    firstSentence = `שלום, ${trimmedName}. ${ratingLine} ושמנו לב שאין ${workplace} אתר רשמי.`;
  } else {
    firstSentence = `שלום, ${trimmedName}. שמנו לב שאין ${workplace} אתר רשמי.`;
  }

  return `${firstSentence}

היום, הצעד הראשון של כל לקוח הוא חיפוש בגוגל – ונוכחות דיגיטלית היא הדרך היחידה לוודא שהרושם הראשוני שהם מקבלים תואם את הרמה המקצועית שלכם. כדי להראות לכם את הפוטנציאל, בנינו עבורכם סקיצה ראשונית:
${url}
כמובן שניתן לערוך ולשדרג, וזו אינה התוצאה הסופית.

אנחנו ב-NovaDigital מציעים כרגע בניית דף נחיתה מקצועי ב-389 ש"ח בלבד (כולל חודש אחסון מתנה). משלמים רק אם מרוצים מהתוצאה.

אם זה רלוונטי, נשמח לשלוח פרטים נוספים.`;
}
