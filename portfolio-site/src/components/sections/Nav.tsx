"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { motion, useScroll, useSpring } from "motion/react";
import Icon from "../Icon";

const links = [
  { href: "#portfolio", label: "פורטפוליו" },
  { href: "#services", label: "שירותים" },
  { href: "#process", label: "תהליך" },
  { href: "#pricing", label: "מחירים" },
  { href: "#contact", label: "צור קשר" },
];

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 28,
    mass: 0.3,
  });

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.nav
      className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-300 ${
        scrolled
          ? "bg-[var(--bg-base)]/85 backdrop-blur-md border-b border-[var(--bg-line)]"
          : "bg-transparent"
      }`}
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.21, 0.6, 0.35, 1] }}
    >
      <div className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="flex items-center justify-between h-16">
          <Link href="#" className="flex items-center gap-2 group">
            <Image
              src="/nova-icon.png"
              alt="Nova Digital"
              width={28}
              height={28}
              className="rounded"
              style={{ width: 28, height: 28 }}
            />
            <span className="text-base font-bold text-white">
              Nova Digital
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="relative text-[var(--text-muted)] hover:text-white transition-colors text-sm"
              >
                {l.label}
              </a>
            ))}
            <a
              href="https://wa.me/972525603365"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white text-black hover:bg-[var(--text-muted)] px-5 py-2 rounded-md text-sm font-semibold transition-colors"
            >
              דברו איתנו
            </a>
          </div>

          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden text-white p-2"
            aria-label="תפריט"
          >
            <Icon name={menuOpen ? "close" : "menu"} size={20} />
          </button>
        </div>
      </div>

      {menuOpen && (
        <motion.div
          className="md:hidden bg-[var(--bg-base)] border-t border-[var(--bg-line)]"
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          transition={{ duration: 0.25 }}
        >
          <div className="px-6 py-5 space-y-3">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setMenuOpen(false)}
                className="block text-[var(--text-muted)] hover:text-white transition-colors text-base py-1.5"
              >
                {l.label}
              </a>
            ))}
            <a
              href="https://wa.me/972525603365"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-center bg-white text-black px-5 py-3 rounded-md font-semibold mt-3"
            >
              דברו איתנו
            </a>
          </div>
        </motion.div>
      )}

      <motion.div
        className="absolute bottom-0 left-0 right-0 h-px origin-left bg-white"
        style={{ scaleX: progress }}
      />
    </motion.nav>
  );
}
