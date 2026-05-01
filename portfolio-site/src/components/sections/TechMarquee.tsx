"use client";

import Marquee from "../Marquee";
import { techStack } from "@/data/tech";

export default function TechMarquee() {
  return (
    <section className="py-14 sm:py-16 relative overflow-hidden border-t border-[var(--bg-line)]">
      <div className="max-w-7xl mx-auto px-6 sm:px-10 mb-8">
        <div className="section-num flex items-center gap-3">
          <strong>—</strong>
          <span className="text-white">טכנולוגיות</span>
          <span className="h-px flex-1 bg-[var(--bg-line)]" />
        </div>
      </div>

      <Marquee speed={40}>
        {techStack.map((tech) => (
          <span
            key={tech}
            className="text-[var(--text-muted)] text-2xl sm:text-3xl font-bold whitespace-nowrap px-6"
          >
            {tech}
            <span className="mx-6 text-[var(--text-dim)]">·</span>
          </span>
        ))}
      </Marquee>
    </section>
  );
}
