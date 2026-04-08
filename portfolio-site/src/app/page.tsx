"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";

/* ───────────────────── Data ───────────────────── */

const portfolioProjects = [
  {
    title: "מסעדת השף",
    description: "אתר תדמית + תפריט דיגיטלי + הזמנת מקומות",
    url: "#",
    tags: ["אתר תדמית", "UI/UX", "הזמנות"],
    color: "from-indigo-500 to-cyan-500",
  },
  {
    title: "סטודיו פילאטיס",
    description: "דף נחיתה + מערכת רישום לשיעורים",
    url: "#",
    tags: ["דף נחיתה", "תשתית", "בריאות"],
    color: "from-fuchsia-500 to-pink-500",
  },
  {
    title: "משרד עורכי דין",
    description: "אתר תדמית + תשתית SEO מלאה",
    url: "#",
    tags: ["אתר תדמית", "SEO", "משפטי"],
    color: "from-blue-500 to-indigo-500",
  },
  {
    title: "חנות אופנה אונליין",
    description: "חנות eCommerce + סליקה + ניהול מלאי",
    url: "#",
    tags: ["eCommerce", "סליקה", "אופנה"],
    color: "from-violet-500 to-purple-500",
  },
  {
    title: "קליניקת שיניים",
    description: "דף נחיתה + מערכת תורים אונליין",
    url: "#",
    tags: ["דף נחיתה", "תורים", "רפואה"],
    isNew: true,
    color: "from-emerald-500 to-cyan-500",
  },
  {
    title: "חברת הובלות",
    description: "אתר תדמית + מחשבון הצעת מחיר אוטומטי",
    url: "#",
    tags: ["אתר תדמית", "אוטומציה", "לוגיסטיקה"],
    isNew: true,
    color: "from-sky-500 to-blue-500",
  },
];

const services = [
  {
    icon: "🌐",
    title: "בניית אתרים ודפי נחיתה",
    description:
      "אתרים מותאמים אישית ב-React & Next.js עם עיצוב פרימיום, טעינה מהירה ותשתית SEO מובנית שמביאה תוצאות.",
    features: ["React & Next.js", "עיצוב UI/UX", "מותאם מובייל", "תשתית SEO"],
  },
  {
    icon: "🤖",
    title: "אוטומציות ו-AI",
    description:
      "סוכני AI, בוטים לוואטסאפ, מענה אוטומטי ללידים ואוטומציות שחוסכות שעות עבודה בכל יום.",
    features: ["סוכני OpenAI", "בוטים לוואטסאפ", "מענה אוטומטי", "חיסכון בזמן"],
  },
  {
    icon: "📊",
    title: "CRM ומערכות ניהול",
    description:
      "מערכות CRM מותאמות אישית לניהול לידים, מעקב אחרי לקוחות ואופטימיזציה של תהליכי המכירה.",
    features: ["ניהול לידים", "מעקב לקוחות", "דוחות חכמים", "אינטגרציות"],
  },
  {
    icon: "🚀",
    title: "קידום דיגיטלי",
    description:
      "קידום אורגני בגוגל, קמפיינים בפייסבוק ואינסטגרם, וניהול Google Ads שמביאים לקוחות איכותיים.",
    features: ["קידום אורגני", "Google Ads", "פייסבוק", "אינסטגרם"],
  },
  {
    icon: "💳",
    title: "סליקה ותשלומים",
    description:
      "חיבור מערכות סליקה מתקדמות, תשלומים אונליין ואינטגרציה עם כל ספקי הסליקה בישראל.",
    features: ["סליקה אונליין", "חשבוניות", "תשלומים בוואטסאפ", "מנויים"],
  },
  {
    icon: "📈",
    title: "אנליטיקס ומעקב",
    description:
      "מעקב מלא אחרי ביצועי האתר, התנהגות משתמשים, קמפיינים ו-ROI עם דשבורדים חכמים.",
    features: ["Google Analytics", "מעקב המרות", "דוחות ROI", "A/B Testing"],
  },
];

const pricingPlans = [
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

const processSteps = [
  {
    step: "01",
    title: "שיחת ייעוץ",
    description: "נבין את העסק שלך, המטרות והקהל — ונתאים פתרון דיגיטלי מדויק.",
  },
  {
    step: "02",
    title: "עיצוב ופיתוח",
    description: "נעצב ונפתח את הנכס הדיגיטלי שלך עם הטכנולוגיות המתקדמות ביותר.",
  },
  {
    step: "03",
    title: "תשתיות ואוטומציה",
    description: "נבנה תשתית SEO, אוטומציות ומערכות שעובדות בשבילך 24/7.",
  },
  {
    step: "04",
    title: "השקה וצמיחה",
    description: "נשיק את הפרויקט ונלווה אותך עם אופטימיזציה שוטפת ותמיכה מלאה.",
  },
];

const techStack = [
  "React",
  "Next.js",
  "Tailwind CSS",
  "TypeScript",
  "Node.js",
  "OpenAI",
  "GSAP",
  "Supabase",
  "Vercel",
  "WhatsApp API",
];

const stats = [
  { value: "50+", label: "פרויקטים" },
  { value: "98%", label: "שביעות רצון" },
  { value: "3x", label: "גידול בלידים" },
  { value: "24/7", label: "אוטומציה" },
];

/* ───────────────── Intersection Observer Hook ───────────────── */

function useInView(threshold = 0.1) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setInView(true);
          obs.disconnect();
        }
      },
      { threshold }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, inView };
}

/* ───────────────── Components ───────────────── */

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = [
    { href: "#portfolio", label: "פורטפוליו" },
    { href: "#services", label: "שירותים" },
    { href: "#process", label: "תהליך עבודה" },
    { href: "#pricing", label: "מחירים" },
    { href: "#contact", label: "צור קשר" },
  ];

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled ? "glass shadow-lg" : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          <a href="#" className="flex items-center gap-2">
            <Image src="/nova-icon.png" alt="Nova Digital" width={36} height={36} className="rounded-lg" />
            <span className="text-lg sm:text-xl font-bold text-white">
              Nova <span className="text-brand-cyan">Digital</span>
            </span>
          </a>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6 lg:gap-8">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-slate-300 hover:text-white transition-colors text-sm font-medium"
              >
                {l.label}
              </a>
            ))}
            <a
              href="https://wa.me/972525603365"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-brand-green hover:brightness-110 text-white px-5 py-2.5 rounded-full text-sm font-bold transition-all shadow-lg shadow-green-500/25"
            >
              דברו איתנו בוואטסאפ
            </a>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden text-white p-2"
            aria-label="תפריט"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {menuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden glass border-t border-white/10">
          <div className="px-4 py-4 space-y-3">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setMenuOpen(false)}
                className="block text-slate-300 hover:text-white transition-colors text-base py-2"
              >
                {l.label}
              </a>
            ))}
            <a
              href="https://wa.me/972525603365"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-center bg-brand-green text-white px-5 py-3 rounded-full font-bold mt-2"
            >
              דברו איתנו בוואטסאפ
            </a>
          </div>
        </div>
      )}
    </nav>
  );
}

function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center grid-bg overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-20 right-20 w-72 h-72 bg-brand-indigo/20 rounded-full blur-[100px] animate-float" />
      <div className="absolute bottom-20 left-20 w-96 h-96 bg-brand-fuchsia/15 rounded-full blur-[120px] animate-float-delayed" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-cyan/10 rounded-full blur-[150px]" />

      <div className="relative max-w-5xl mx-auto px-4 sm:px-6 text-center pt-24 pb-16">
        <div className="mb-8 animate-float">
          <Image
            src="/nova-icon-small.png"
            alt="Nova Digital"
            width={500}
            height={273}
            className="mx-auto rounded-xl"
            priority
          />
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-7xl font-black leading-tight mb-6">
          נכסים דיגיטליים
          <br />
          <span className="gradient-text">פרימיום שמניבים</span>
          <br />
          תוצאות
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          אנחנו בונים אתרים, דפי נחיתה ומערכות אוטומציה עם הטכנולוגיות
          המתקדמות ביותר — כדי שהעסק שלך יצמח.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <a
            href="https://wa.me/972525603365"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-brand-green hover:brightness-110 text-white px-8 py-4 rounded-full text-lg font-bold transition-all shadow-lg shadow-green-500/25 flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
              <path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.612.638l4.648-1.408A11.953 11.953 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.387 0-4.592-.8-6.363-2.147l-.178-.14-3.693 1.12 1.178-3.534-.154-.184A9.96 9.96 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
            </svg>
            שיחת ייעוץ חינם
          </a>
          <a
            href="#portfolio"
            className="border border-white/20 hover:border-white/40 text-white px-8 py-4 rounded-full text-lg font-medium transition-all hover:bg-white/5"
          >
            צפו בעבודות שלנו
          </a>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-3xl mx-auto">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-3xl sm:text-4xl font-black gradient-text mb-1">{s.value}</div>
              <div className="text-sm text-slate-400">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  );
}

function PortfolioSection() {
  const { ref, inView } = useInView();

  return (
    <section id="portfolio" className="py-20 sm:py-28 relative" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="text-brand-cyan text-sm font-bold tracking-wider uppercase">
            פורטפוליו
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mt-3 mb-4">
            הפרויקטים <span className="gradient-text">שלנו</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-lg">
            כל פרויקט נבנה עם תשתיות מתקדמות, עיצוב פרימיום ו-SEO מובנה
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {portfolioProjects.map((project, i) => (
            <a
              key={project.title}
              href={project.url}
              target="_blank"
              rel="noopener noreferrer"
              className={`portfolio-card relative group bg-slate-mid/50 border border-white/5 rounded-2xl overflow-hidden ${
                inView ? "animate-fade-up" : "opacity-0"
              }`}
              style={{ animationDelay: `${i * 100}ms` }}
            >
              {/* Gradient header */}
              <div
                className={`h-44 bg-gradient-to-br ${project.color} flex items-center justify-center relative overflow-hidden`}
              >
                <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors" />
                <span className="relative text-white text-2xl font-black drop-shadow-lg">
                  {project.title}
                </span>
                {project.isNew && (
                  <span className="absolute top-3 left-3 badge-new text-white text-xs font-bold px-3 py-1 rounded-full">
                    NEW
                  </span>
                )}
              </div>

              {/* Content */}
              <div className="p-5">
                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-brand-cyan transition-colors">
                  {project.title}
                </h3>
                <p className="text-slate-400 text-sm mb-4">{project.description}</p>
                <div className="flex flex-wrap gap-2">
                  {project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="bg-white/5 border border-white/10 text-slate-300 text-xs px-3 py-1 rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Hover arrow */}
              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

function ServicesSection() {
  const { ref, inView } = useInView();

  return (
    <section id="services" className="py-20 sm:py-28 relative grid-bg" ref={ref}>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-indigo/5 to-transparent" />
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="text-brand-fuchsia text-sm font-bold tracking-wider uppercase">
            שירותים
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mt-3 mb-4">
            מה אנחנו <span className="gradient-text">עושים</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-lg">
            פתרונות דיגיטליים מקצה לקצה שמניבים תוצאות אמיתיות
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {services.map((service, i) => (
            <div
              key={service.title}
              className={`group bg-slate-mid/40 border border-white/5 rounded-2xl p-6 sm:p-7 hover:border-brand-indigo/30 transition-all duration-300 hover:-translate-y-2 ${
                inView ? "animate-fade-up" : "opacity-0"
              }`}
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="text-4xl mb-4">{service.icon}</div>
              <h3 className="text-xl font-bold text-white mb-3 group-hover:text-brand-cyan transition-colors">
                {service.title}
              </h3>
              <p className="text-slate-400 text-sm leading-relaxed mb-5">
                {service.description}
              </p>
              <div className="flex flex-wrap gap-2">
                {service.features.map((f) => (
                  <span
                    key={f}
                    className="bg-brand-indigo/10 text-brand-cyan text-xs px-3 py-1 rounded-full border border-brand-indigo/20"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TechStackSection() {
  return (
    <section className="py-16 sm:py-20 border-y border-white/5">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center">
        <span className="text-brand-cyan text-sm font-bold tracking-wider uppercase">
          טכנולוגיות
        </span>
        <h2 className="text-2xl sm:text-3xl font-bold text-white mt-3 mb-10">
          הכלים שאנחנו <span className="gradient-text">עובדים איתם</span>
        </h2>
        <div className="flex flex-wrap justify-center gap-3 sm:gap-4">
          {techStack.map((tech) => (
            <span
              key={tech}
              className="bg-white/5 border border-white/10 text-slate-300 px-5 py-2.5 rounded-full text-sm font-medium hover:border-brand-indigo/40 hover:bg-brand-indigo/10 hover:text-white transition-all cursor-default"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

function ProcessSection() {
  const { ref, inView } = useInView();

  return (
    <section id="process" className="py-20 sm:py-28" ref={ref}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="text-brand-cyan text-sm font-bold tracking-wider uppercase">
            תהליך עבודה
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mt-3 mb-4">
            איך זה <span className="gradient-text">עובד</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-lg">
            תהליך מסודר ושקוף מהרגע הראשון
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 lg:gap-8">
          {processSteps.map((step, i) => (
            <div
              key={step.step}
              className={`relative bg-slate-mid/40 border border-white/5 rounded-2xl p-6 sm:p-8 hover:border-brand-indigo/30 transition-all duration-300 ${
                inView ? "animate-fade-up" : "opacity-0"
              }`}
              style={{ animationDelay: `${i * 150}ms` }}
            >
              <span className="text-5xl sm:text-6xl font-black text-brand-indigo/20 absolute top-4 left-4">
                {step.step}
              </span>
              <div className="relative">
                <h3 className="text-xl font-bold text-white mb-3 mt-2">{step.title}</h3>
                <p className="text-slate-400 leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PricingSection() {
  const { ref, inView } = useInView();

  return (
    <section id="pricing" className="py-20 sm:py-28 grid-bg relative" ref={ref}>
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-fuchsia/5 to-transparent" />
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="text-brand-fuchsia text-sm font-bold tracking-wider uppercase">
            מחירים
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mt-3 mb-4">
            חבילות <span className="gradient-text">אוטומציה</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-lg">
            בחרו את החבילה שמתאימה לעסק שלכם
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {pricingPlans.map((plan, i) => (
            <div
              key={plan.name}
              className={`relative bg-slate-mid/50 border ${plan.color} rounded-2xl p-6 sm:p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl ${plan.glow} ${
                inView ? "animate-fade-up" : "opacity-0"
              } ${plan.popular ? "ring-2 ring-brand-indigo/50 scale-[1.02]" : ""}`}
              style={{ animationDelay: `${i * 150}ms` }}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-brand-indigo to-brand-fuchsia text-white text-xs font-bold px-4 py-1.5 rounded-full">
                  הכי פופולרי
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                <p className="text-sm text-slate-400 mt-1">{plan.subtitle}</p>
                <div className="mt-4">
                  <span className="text-4xl sm:text-5xl font-black text-white">{plan.price}</span>
                  <span className="text-lg text-slate-400 mr-1">₪</span>
                  <span className="text-sm text-slate-500 block mt-1">
                    {plan.period}
                  </span>
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-slate-300">
                    <svg className="w-4 h-4 text-brand-cyan flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>

              <a
                href="https://wa.me/972525603365"
                target="_blank"
                rel="noopener noreferrer"
                className={`block text-center py-3 rounded-full font-bold text-sm transition-all ${
                  plan.popular
                    ? "bg-gradient-to-r from-brand-indigo to-brand-fuchsia text-white hover:brightness-110 shadow-lg"
                    : "bg-white/5 border border-white/10 text-white hover:bg-white/10"
                }`}
              >
                התחילו עכשיו
              </a>
            </div>
          ))}
        </div>

        {/* Special offer */}
        <div className="mt-12 text-center">
          <div className="inline-block bg-gradient-to-r from-brand-indigo/20 to-brand-fuchsia/20 border border-brand-indigo/30 rounded-2xl p-6 sm:p-8 max-w-2xl">
            <div className="text-brand-cyan font-bold text-sm mb-2">מבצע השקה</div>
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">
              דף נחיתה איכותי מ-299₪ + מע&quot;מ
            </h3>
            <p className="text-slate-400 text-sm">
              ל-100 העסקים הראשונים בלבד — כולל תשתית SEO מלאה, עיצוב פרימיום ואופטימיזציה למובייל
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

const SUPABASE_URL = "https://vinpsfqldlfcgbdajvym.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpbnBzZnFsZGxmY2diZGFqdnltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0Nzc5NjcsImV4cCI6MjA5MTA1Mzk2N30.8wmUv3OoKZItN9Jb9Yf3HGvySJaoSXLxiPIpDK-Hv3w";

function ContactSection() {
  const [formData, setFormData] = useState({ name: "", phone: "", message: "" });
  const [submitted, setSubmitted] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    // Save to Supabase
    try {
      await fetch(`${SUPABASE_URL}/rest/v1/contact_leads`, {
        method: "POST",
        headers: {
          apikey: SUPABASE_ANON_KEY,
          Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify({
          name: formData.name,
          phone: formData.phone,
          message: formData.message || "",
          source: "website",
        }),
      });
    } catch {
      // Don't block WA if Supabase fails
    }

    // Open WhatsApp
    const text = `שלום, שמי ${formData.name}. ${formData.message || "אשמח לשמוע פרטים נוספים"}`;
    window.open(
      `https://wa.me/972525603365?text=${encodeURIComponent(text)}`,
      "_blank"
    );
    setSaving(false);
    setSubmitted(true);
  };

  return (
    <section id="contact" className="py-20 sm:py-28 relative">
      <div className="absolute inset-0 bg-gradient-to-t from-brand-indigo/10 via-transparent to-transparent" />
      <div className="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <span className="text-brand-green text-sm font-bold tracking-wider uppercase">
            צור קשר
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mt-3 mb-4">
            בואו <span className="gradient-text">נדבר</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-lg">
            השאירו פרטים ונחזור אליכם תוך דקות
          </p>
        </div>

        <div className="bg-slate-mid/50 border border-white/5 rounded-2xl p-6 sm:p-10">
          {submitted ? (
            <div className="text-center py-8">
              <div className="text-5xl mb-4">&#x2705;</div>
              <h3 className="text-2xl font-bold text-white mb-2">תודה!</h3>
              <p className="text-slate-400">נפתח לכם חלון וואטסאפ — שלחו לנו הודעה ונחזור אליכם מיד.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">שם מלא</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo/50 focus:ring-1 focus:ring-brand-indigo/50 transition-colors"
                  placeholder="הכנס את שמך"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">טלפון</label>
                <input
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo/50 focus:ring-1 focus:ring-brand-indigo/50 transition-colors"
                  placeholder="050-000-0000"
                  dir="ltr"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  ספרו לנו על העסק שלכם
                </label>
                <textarea
                  rows={4}
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-brand-indigo/50 focus:ring-1 focus:ring-brand-indigo/50 transition-colors resize-none"
                  placeholder="מה העסק שלכם עושה? מה אתם מחפשים?"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="w-full bg-gradient-to-r from-brand-indigo to-brand-fuchsia hover:brightness-110 text-white py-4 rounded-full text-lg font-bold transition-all shadow-lg animate-pulse-glow disabled:opacity-60"
              >
                {saving ? "שומר..." : "שלחו הודעה בוואטסאפ"}
              </button>
            </form>
          )}
        </div>

        {/* Direct contact */}
        <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4 sm:gap-6 text-center">
          <a
            href="tel:0525603365"
            className="flex items-center justify-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            052-560-3365
          </a>
          <a
            href="https://wa.me/972525603365"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 text-brand-green hover:brightness-110 transition-all"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
            </svg>
            וואטסאפ
          </a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/5 py-10 sm:py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Image src="/nova-icon.png" alt="Nova Digital" width={32} height={32} className="rounded-lg" />
            <span className="text-lg font-bold text-white">
              Nova <span className="text-brand-cyan">Digital</span>
            </span>
          </div>

          <div className="flex items-center gap-6 text-sm text-slate-400">
            <a href="#portfolio" className="hover:text-white transition-colors">פורטפוליו</a>
            <a href="#services" className="hover:text-white transition-colors">שירותים</a>
            <a href="#pricing" className="hover:text-white transition-colors">מחירים</a>
            <a href="#contact" className="hover:text-white transition-colors">צור קשר</a>
          </div>

          <div className="flex items-center gap-4 text-sm text-slate-500">
            <a href="/privacy" className="hover:text-slate-300 transition-colors">מדיניות פרטיות</a>
            <a href="/terms" className="hover:text-slate-300 transition-colors">תנאי שימוש</a>
            <a href="/accessibility" className="hover:text-slate-300 transition-colors">הצהרת נגישות</a>
          </div>

          <div className="text-sm text-slate-500">
            &copy; {new Date().getFullYear()} Nova Digital — נובה דיגיטל
          </div>
        </div>
      </div>
    </footer>
  );
}

/* ─────────── Cookie Consent Banner ─────────── */

function CookieConsent() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("cookie_consent")) {
      setShow(true);
    }
  }, []);

  const accept = () => {
    localStorage.setItem("cookie_consent", "accepted");
    setShow(false);
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4">
      <div className="max-w-4xl mx-auto glass rounded-2xl p-5 sm:p-6 flex flex-col sm:flex-row items-center gap-4 shadow-2xl border border-white/10">
        <p className="text-sm text-slate-300 flex-1 text-center sm:text-right">
          אתר זה משתמש בעוגיות (cookies) לצורך שיפור חוויית המשתמש וניתוח תנועה באתר.
          למידע נוסף ראו את{" "}
          <a href="/privacy" className="text-brand-cyan hover:underline">
            מדיניות הפרטיות
          </a>{" "}
          שלנו.
        </p>
        <div className="flex gap-3">
          <button
            onClick={accept}
            className="bg-brand-indigo hover:brightness-110 text-white px-6 py-2 rounded-full text-sm font-bold transition-all"
          >
            מאשר
          </button>
          <button
            onClick={accept}
            className="bg-white/5 border border-white/10 text-white px-6 py-2 rounded-full text-sm font-medium hover:bg-white/10 transition-all"
          >
            סגור
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─────────── Floating WhatsApp Button ─────────── */

function FloatingWhatsApp() {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 3000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;
  return (
    <a
      href="https://wa.me/972525603365"
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-6 left-6 z-50 bg-brand-green hover:brightness-110 text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg shadow-green-500/30 transition-all hover:scale-110 animate-fade-up"
      aria-label="WhatsApp"
    >
      <svg className="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
        <path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.612.638l4.648-1.408A11.953 11.953 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.387 0-4.592-.8-6.363-2.147l-.178-.14-3.693 1.12 1.178-3.534-.154-.184A9.96 9.96 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
      </svg>
    </a>
  );
}

/* ───────────────── Main Page ───────────────── */

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <PortfolioSection />
        <TechStackSection />
        <ServicesSection />
        <ProcessSection />
        <PricingSection />
        <ContactSection />
      </main>
      <Footer />
      <FloatingWhatsApp />
      <CookieConsent />
    </>
  );
}
