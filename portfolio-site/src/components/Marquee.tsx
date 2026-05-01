"use client";

import { type ReactNode } from "react";

type MarqueeProps = {
  children: ReactNode;
  className?: string;
  reverse?: boolean;
  speed?: number;
  fade?: boolean;
};

export default function Marquee({
  children,
  className,
  reverse,
  speed = 30,
  fade = true,
}: MarqueeProps) {
  return (
    <div
      className={`relative overflow-hidden ${className ?? ""}`}
      style={
        fade
          ? {
              maskImage:
                "linear-gradient(90deg, transparent, black 10%, black 90%, transparent)",
              WebkitMaskImage:
                "linear-gradient(90deg, transparent, black 10%, black 90%, transparent)",
            }
          : undefined
      }
    >
      <div
        className="marquee-track flex w-max gap-4"
        style={{
          animationDuration: `${speed}s`,
          animationDirection: reverse ? "reverse" : "normal",
        }}
      >
        <div className="flex shrink-0 gap-4 items-center">{children}</div>
        <div className="flex shrink-0 gap-4 items-center" aria-hidden>
          {children}
        </div>
      </div>
    </div>
  );
}
