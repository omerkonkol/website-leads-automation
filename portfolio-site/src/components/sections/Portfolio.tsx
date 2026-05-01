"use client";

import Image from "next/image";
import { motion } from "motion/react";
import { RevealStagger, staggerItem } from "../Reveal";
import SectionHeader from "../SectionHeader";
import Icon from "../Icon";
import { portfolioProjects } from "@/data/portfolio";

export default function Portfolio() {
  return (
    <section id="portfolio" className="py-20 sm:py-28 relative">
      <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
        <SectionHeader
          num="01"
          label="פורטפוליו"
          title={
            <>
              הפרויקטים <span className="text-[var(--text-muted)]">שלנו</span>
            </>
          }
          description="כל פרויקט נבנה עם תשתיות מתקדמות, עיצוב פרימיום ו-SEO מובנה."
        />

        <RevealStagger
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5"
          stagger={0.06}
        >
          {portfolioProjects.map((project) => (
            <motion.a
              key={project.title}
              variants={staggerItem}
              href={project.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative block"
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 220, damping: 22 }}
            >
              <div className="relative bg-[var(--bg-elev)] rounded-xl overflow-hidden border border-[var(--bg-line)] group-hover:border-white/30 transition-colors">
                <div className="relative aspect-[4/3] overflow-hidden bg-black">
                  {project.image ? (
                    <>
                      <Image
                        src={project.image}
                        alt={project.title}
                        fill
                        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                        className="object-cover object-center transition-transform duration-700 group-hover:scale-[1.04]"
                      />
                      {/* Bottom mask hides Gemini watermark + softens transition to card body */}
                      <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-[var(--bg-elev)] via-[var(--bg-elev)]/80 to-transparent" />
                    </>
                  ) : (
                    <PlaceholderArt title={project.title} />
                  )}
                  {project.isNew && (
                    <span className="absolute top-3 left-3 badge-new text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider z-10">
                      חדש
                    </span>
                  )}
                  <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-white/10 backdrop-blur-sm text-white">
                      <Icon name="arrow-up-right" size={14} />
                    </span>
                  </div>
                </div>

                <div className="p-5">
                  <h3 className="text-base font-bold text-white mb-1.5">
                    {project.title}
                  </h3>
                  <p className="text-[var(--text-muted)] text-sm mb-4 leading-relaxed">
                    {project.description}
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {project.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[11px] text-[var(--text-muted)] px-2 py-0.5 border border-[var(--bg-line)] rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </motion.a>
          ))}
        </RevealStagger>
      </div>
    </section>
  );
}

function PlaceholderArt({ title }: { title: string }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-[var(--bg-base)]">
      <div className="absolute inset-0 opacity-40" style={{
        backgroundImage:
          "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
        backgroundSize: "24px 24px",
      }} />
      <div className="relative text-center px-4">
        <div className="text-[var(--text-dim)] text-[10px] uppercase tracking-[0.2em] mb-2">
          בקרוב
        </div>
        <div className="text-white text-lg font-bold">
          {title}
        </div>
      </div>
    </div>
  );
}
