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
              className={`group relative block ${
                project.span === "wide" ? "sm:col-span-2 lg:col-span-2" : ""
              }`}
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 220, damping: 22 }}
            >
              <div className="relative bg-[var(--bg-elev)] rounded-xl overflow-hidden border border-[var(--bg-line)]">
                <div
                  className={`relative overflow-hidden ${
                    project.span === "wide" ? "h-56 sm:h-72" : "h-44 sm:h-52"
                  }`}
                >
                  {project.image ? (
                    <>
                      <Image
                        src={project.image}
                        alt={project.title}
                        fill
                        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                        className="object-cover transition-transform duration-700 group-hover:scale-105"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
                    </>
                  ) : (
                    <>
                      <div
                        className={`absolute inset-0 bg-gradient-to-br ${project.color}`}
                      />
                      <div className="absolute inset-0 bg-black/30 group-hover:bg-black/10 transition-colors" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-white text-xl font-bold drop-shadow">
                          {project.title}
                        </span>
                      </div>
                    </>
                  )}
                  {project.isNew && (
                    <span className="absolute top-3 left-3 badge-new text-[11px] font-bold px-2 py-1 rounded uppercase tracking-wider z-10">
                      חדש
                    </span>
                  )}
                </div>

                <div className="p-5">
                  <h3 className="text-base font-bold text-white mb-2">
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

                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-white/10 backdrop-blur-sm text-white">
                    <Icon name="arrow-up-right" size={14} />
                  </span>
                </div>
              </div>
            </motion.a>
          ))}
        </RevealStagger>
      </div>
    </section>
  );
}
