export type Testimonial = {
  quote: string;
  author: string;
  role: string;
  accent: string;
};

// Placeholder testimonials — replace with real customer quotes when available.
export const testimonials: Testimonial[] = [
  {
    quote:
      "האתר החדש שיצרו לנו הוריד את כמות הפניות בטלפון ב-40% — הלקוחות מקבלים את כל המידע באתר.",
    author: "דנה לוי",
    role: "בעלת סטודיו פילאטיס",
    accent: "from-fuchsia-500 to-pink-500",
  },
  {
    quote:
      "תוך שבועיים מהשקה התחלנו לקבל לידים איכותיים מגוגל. תשתית ה-SEO באמת עובדת.",
    author: "אבי כהן",
    role: "מנהל משרד עורכי דין",
    accent: "from-blue-500 to-indigo-500",
  },
  {
    quote:
      "האוטומציה של הוואטסאפ חוסכת לנו שעתיים ביום. הבוט עונה ללקוחות ב-24/7 ואני מקבל רק את הלידים החמים.",
    author: "יוסי ברק",
    role: "בעל מסעדה",
    accent: "from-indigo-500 to-cyan-500",
  },
  {
    quote:
      "עיצוב פרימיום, ביצועים מצוינים, ושירות שלא מצאתי באף סטודיו אחר. ממליץ בחום.",
    author: "מיכל אברהם",
    role: "מנהלת חנות אונליין",
    accent: "from-violet-500 to-purple-500",
  },
  {
    quote:
      "ה-CRM שהם בנו לנו פשוט שינה את הדרך שאנחנו עובדים. כל הלידים במקום אחד, מסונכרן עם וואטסאפ.",
    author: "רן שמש",
    role: "מנכ״ל חברת הובלות",
    accent: "from-sky-500 to-blue-500",
  },
];
