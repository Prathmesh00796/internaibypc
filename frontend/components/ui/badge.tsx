import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border",
  {
    variants: {
      variant: {
        neutral: "bg-base-elevated text-ink-secondary border-base-border",
        violet: "bg-signal-violet/10 text-signal-violet border-signal-violet/30",
        teal: "bg-signal-teal/10 text-signal-teal border-signal-teal/30",
        amber: "bg-signal-amber/10 text-signal-amber border-signal-amber/30",
        coral: "bg-signal-coral/10 text-signal-coral border-signal-coral/30",
      },
    },
    defaultVariants: { variant: "neutral" },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant, className }))} {...props} />;
}

export { Badge, badgeVariants };
