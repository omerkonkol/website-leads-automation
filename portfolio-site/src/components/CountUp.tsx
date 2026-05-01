"use client";

import {
  useInView,
  useMotionValue,
  useSpring,
  useTransform,
  useReducedMotion,
} from "motion/react";
import { useEffect, useRef } from "react";

type CountUpProps = {
  to: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
};

export default function CountUp({
  to,
  duration = 1.6,
  prefix,
  suffix,
  className,
}: CountUpProps) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.4 });
  const value = useMotionValue(0);
  const spring = useSpring(value, {
    duration: duration * 1000,
    bounce: 0,
  });
  const display = useTransform(spring, (v) => Math.round(v).toLocaleString("he-IL"));
  const textRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!inView) return;
    if (reduce) {
      value.set(to);
      return;
    }
    value.set(to);
  }, [inView, to, value, reduce]);

  useEffect(() => {
    return display.on("change", (latest) => {
      if (textRef.current) textRef.current.textContent = latest;
    });
  }, [display]);

  return (
    <span ref={ref} className={className}>
      {prefix}
      <span ref={textRef}>0</span>
      {suffix}
    </span>
  );
}
