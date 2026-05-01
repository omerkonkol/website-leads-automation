export type PortfolioProject = {
  title: string;
  description: string;
  url: string;
  tags: string[];
  color: string;
  image?: string;
  isNew?: boolean;
  span?: "wide";
};

export const portfolioProjects: PortfolioProject[] = [
  {
    title: "סטודיו פילאטיס",
    description: "דף נחיתה + מערכת רישום לשיעורים",
    url: "#",
    tags: ["דף נחיתה", "תשתית", "בריאות"],
    color: "from-fuchsia-500 to-pink-500",
    image: "/portfolio/pilates.png",
  },
  {
    title: "משרד עורכי דין",
    description: "אתר תדמית + תשתית SEO מלאה",
    url: "#",
    tags: ["אתר תדמית", "SEO", "משפטי"],
    color: "from-blue-500 to-indigo-500",
    image: "/portfolio/law.png",
  },
  {
    title: "קליניקת שיניים",
    description: "דף נחיתה + מערכת תורים אונליין",
    url: "#",
    tags: ["דף נחיתה", "תורים", "רפואה"],
    isNew: true,
    color: "from-emerald-500 to-cyan-500",
    image: "/portfolio/dental.png",
  },
  {
    title: "חברת הובלות",
    description: "אתר תדמית + מחשבון הצעת מחיר אוטומטי",
    url: "#",
    tags: ["אתר תדמית", "אוטומציה", "לוגיסטיקה"],
    isNew: true,
    color: "from-sky-500 to-blue-500",
    image: "/portfolio/logistics.png",
  },
  {
    title: "מסעדת השף",
    description: "אתר תדמית + תפריט דיגיטלי + הזמנת מקומות",
    url: "#",
    tags: ["אתר תדמית", "UI/UX", "הזמנות"],
    color: "from-indigo-500 to-cyan-500",
  },
  {
    title: "חנות אופנה אונליין",
    description: "חנות eCommerce + סליקה + ניהול מלאי",
    url: "#",
    tags: ["eCommerce", "סליקה", "אופנה"],
    color: "from-violet-500 to-purple-500",
  },
];
