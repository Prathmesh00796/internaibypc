"use client";

import { cn } from "@/lib/utils";

interface MatchScoreRingProps {
  score: number; // 0-100
  size?: number;
  strokeWidth?: number;
  className?: string;
}

function tierColor(score: number): string {
  if (score >= 90) return "#2DD4BF"; // teal
  if (score >= 70) return "#7C6CF6"; // violet
  if (score >= 50) return "#F5A524"; // amber
  return "#5C6478"; // muted
}

export function MatchScoreRing({ score, size = 56, strokeWidth = 4, className }: MatchScoreRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = tierColor(score);

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#242938"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1)" }}
        />
      </svg>
      <span
        className="absolute font-mono font-semibold tabular-nums"
        style={{ fontSize: size * 0.28, color }}
      >
        {Math.round(score)}
      </span>
    </div>
  );
}
