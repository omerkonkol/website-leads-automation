export type Stat = {
  value: number;
  suffix?: string;
  prefix?: string;
  label: string;
};

export const stats: Stat[] = [
  { value: 50, suffix: "+", label: "פרויקטים" },
  { value: 98, suffix: "%", label: "שביעות רצון" },
  { value: 3, suffix: "x", label: "גידול בלידים" },
  { value: 24, suffix: "/7", label: "אוטומציה" },
];
