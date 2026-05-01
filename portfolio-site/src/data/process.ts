import type { IconName } from "@/components/Icon";

export type ProcessStep = {
  step: string;
  title: string;
  description: string;
  icon: IconName;
};

export const processSteps: ProcessStep[] = [
  {
    step: "01",
    title: "שיחת ייעוץ",
    description: "נבין את העסק שלך, המטרות והקהל — ונתאים פתרון דיגיטלי מדויק.",
    icon: "chat",
  },
  {
    step: "02",
    title: "עיצוב ופיתוח",
    description: "נעצב ונפתח את הנכס הדיגיטלי שלך עם הטכנולוגיות המתקדמות ביותר.",
    icon: "palette",
  },
  {
    step: "03",
    title: "תשתיות ואוטומציה",
    description: "נבנה תשתית SEO, אוטומציות ומערכות שעובדות בשבילך 24/7.",
    icon: "gear",
  },
  {
    step: "04",
    title: "השקה וצמיחה",
    description: "נשיק את הפרויקט ונלווה אותך עם אופטימיזציה שוטפת ותמיכה מלאה.",
    icon: "launch",
  },
];
