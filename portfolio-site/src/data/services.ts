import type { IconName } from "@/components/Icon";

export type Service = {
  icon: IconName;
  title: string;
  description: string;
  features: string[];
};

export const services: Service[] = [
  {
    icon: "globe",
    title: "בניית אתרים ודפי נחיתה",
    description:
      "אתרים מותאמים אישית ב-React & Next.js עם עיצוב פרימיום, טעינה מהירה ותשתית SEO מובנית שמביאה תוצאות.",
    features: ["React & Next.js", "עיצוב UI/UX", "מותאם מובייל", "תשתית SEO"],
  },
  {
    icon: "bot",
    title: "אוטומציות ו-AI",
    description:
      "סוכני AI, בוטים לוואטסאפ, מענה אוטומטי ללידים ואוטומציות שחוסכות שעות עבודה בכל יום.",
    features: ["סוכני OpenAI", "בוטים לוואטסאפ", "מענה אוטומטי", "חיסכון בזמן"],
  },
  {
    icon: "chart",
    title: "CRM ומערכות ניהול",
    description:
      "מערכות CRM מותאמות אישית לניהול לידים, מעקב אחרי לקוחות ואופטימיזציה של תהליכי המכירה.",
    features: ["ניהול לידים", "מעקב לקוחות", "דוחות חכמים", "אינטגרציות"],
  },
  {
    icon: "rocket",
    title: "קידום דיגיטלי",
    description:
      "קידום אורגני בגוגל, קמפיינים בפייסבוק ואינסטגרם, וניהול Google Ads שמביאים לקוחות איכותיים.",
    features: ["קידום אורגני", "Google Ads", "פייסבוק", "אינסטגרם"],
  },
  {
    icon: "card",
    title: "סליקה ותשלומים",
    description:
      "חיבור מערכות סליקה מתקדמות, תשלומים אונליין ואינטגרציה עם כל ספקי הסליקה בישראל.",
    features: ["סליקה אונליין", "חשבוניות", "תשלומים בוואטסאפ", "מנויים"],
  },
  {
    icon: "analytics",
    title: "אנליטיקס ומעקב",
    description:
      "מעקב מלא אחרי ביצועי האתר, התנהגות משתמשים, קמפיינים ו-ROI עם דשבורדים חכמים.",
    features: ["Google Analytics", "מעקב המרות", "דוחות ROI", "A/B Testing"],
  },
];
