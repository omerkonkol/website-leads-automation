import type { Metadata } from "next";
import { Heebo } from "next/font/google";
import "./globals.css";

const heebo = Heebo({
  subsets: ["latin", "hebrew"],
  variable: "--font-heebo-var",
});

export const icons = {
  icon: "/favicon.svg",
};

export const metadata: Metadata = {
  title: "Nova Digital | נובה דיגיטל - נכסים דיגיטליים פרימיום לעסקים",
  description:
    "בניית אתרים, דפי נחיתה, אוטומציות, CRM וקידום דיגיטלי לעסקים. React, Next.js, AI ותשתיות SEO מתקדמות. נובה דיגיטל.",
  keywords: [
    "בניית אתרים",
    "דפי נחיתה",
    "קידום אורגני",
    "CRM",
    "אוטומציה",
    "עיצוב אתרים",
    "נובה דיגיטל",
  ],
  openGraph: {
    title: "Nova Digital | נובה דיגיטל - נכסים דיגיטליים פרימיום",
    description: "נכסים דיגיטליים פרימיום שמניבים תוצאות — נובה דיגיטל",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="he" dir="rtl" className={`${heebo.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-[family-name:var(--font-heebo-var)]">
        {children}
      </body>
    </html>
  );
}
