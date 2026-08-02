"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, Briefcase, ListChecks, User, FileText,
  BarChart3, Bell, LogOut, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { clearAuthTokens } from "@/lib/api-client";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/jobs", label: "Find Jobs", icon: Briefcase },
  { href: "/queue", label: "Review Queue", icon: ListChecks },
  { href: "/applications", label: "Applications", icon: FileText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/profile", label: "Profile", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    clearAuthTokens();
    router.push("/login");
  }

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 flex flex-col border-r border-base-border bg-base/80 backdrop-blur-xl">
      <div className="flex items-center gap-2 px-6 py-6">
        <div className="w-8 h-8 rounded-lg bg-signal-violet/20 border border-signal-violet/40 flex items-center justify-center">
          <Sparkles size={16} className="text-signal-violet" />
        </div>
        <span className="font-display font-semibold text-lg">InternAI</span>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-signal-violet/10 text-signal-violet border border-signal-violet/20"
                  : "text-ink-secondary hover:text-ink-primary hover:bg-base-elevated border border-transparent"
              )}
            >
              <Icon size={17} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-6 space-y-1">
        <Link
          href="/notifications"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-ink-secondary hover:text-ink-primary hover:bg-base-elevated transition-colors"
        >
          <Bell size={17} />
          Notifications
        </Link>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-ink-secondary hover:text-signal-coral hover:bg-signal-coral/10 transition-colors"
        >
          <LogOut size={17} />
          Log out
        </button>
      </div>
    </aside>
  );
}
