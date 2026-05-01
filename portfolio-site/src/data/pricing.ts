export type PricingPlan = {
  name: string;
  subtitle: string;
  price: string;
  period: string;
  popular?: boolean;
  features: string[];
  color: string;
  glow: string;
};

export const pricingPlans: PricingPlan[] = [
  {
    name: "בייסיק",
    subtitle: "אימייל",
    price: "99",
    period: "לחודש",
    features: [
      "לכידת לידים אוטומטית",
      "מענה אוטומטי במייל",
      "טופס לידים באתר",
      "גיבוי לידים",
      "דוחות חודשיים",
    ],
    color: "border-cyan-500/30",
    glow: "hover:shadow-cyan-500/20",
  },
  {
    name: "פרו",
    subtitle: "וואטסאפ",
    price: "150",
    period: "לחודש",
    popular: true,
    features: [
      "כל מה שבבייסיק",
      "אוטומציית וואטסאפ",
      "בוט חכם למענה",
      "שליחת הצעות מחיר",
      "0₪ דמי הקמה (במקום 600₪)",
    ],
    color: "border-brand-indigo/50",
    glow: "hover:shadow-indigo-500/20",
  },
  {
    name: "פרימיום",
    subtitle: "CRM + סושיאל",
    price: "250",
    period: "לחודש",
    features: [
      "כל מה שבפרו",
      "מערכת CRM מלאה",
      "אינטגרציית פייסבוק",
      "אינטגרציית אינסטגרם",
      "ניהול לידים מתקדם",
    ],
    color: "border-fuchsia-500/30",
    glow: "hover:shadow-fuchsia-500/20",
  },
];
