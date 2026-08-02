"use client";

import { useEffect, useState } from "react";
import { Briefcase, FileText, Send, Clock, TrendingUp, Users, XCircle, Award } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api-client";
import { DashboardStats, AnalyticsOverview } from "@/lib/types";

const STAT_CARDS = [
  { key: "total_jobs_found", label: "Jobs found", icon: Briefcase, color: "text-signal-violet" },
  { key: "applications_prepared", label: "Prepared", icon: FileText, color: "text-ink-primary" },
  { key: "applications_submitted", label: "Submitted", icon: Send, color: "text-signal-teal" },
  { key: "pending_review", label: "Pending review", icon: Clock, color: "text-signal-amber" },
  { key: "response_rate", label: "Response rate", icon: TrendingUp, color: "text-signal-violet", suffix: "%" },
  { key: "interviews", label: "Interviews", icon: Users, color: "text-signal-teal" },
  { key: "offers", label: "Offers", icon: Award, color: "text-signal-teal" },
  { key: "rejections", label: "Rejections", icon: XCircle, color: "text-signal-coral" },
] as const;

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get("/dashboard/stats"), api.get("/dashboard/analytics")])
      .then(([statsRes, analyticsRes]) => {
        setStats(statsRes.data);
        setAnalytics(analyticsRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-ink-secondary mt-1">Your search, at a glance.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {STAT_CARDS.map((card) => {
          const Icon = card.icon;
          const value = stats ? stats[card.key as keyof DashboardStats] : undefined;
          return (
            <Card key={card.key} className="p-5">
              <div className="flex items-center justify-between mb-3">
                <Icon size={16} className={card.color} />
              </div>
              <div className="stat-number text-2xl">
                {loading ? (
                  <span className="inline-block w-12 h-6 bg-base-elevated rounded animate-pulse" />
                ) : (
                  <>
                    {value ?? 0}
                    {"suffix" in card ? card.suffix : ""}
                  </>
                )}
              </div>
              <div className="text-xs text-ink-secondary mt-1">{card.label}</div>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Applications over time</CardTitle>
        </CardHeader>
        <CardContent>
          {analytics && analytics.daily.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={analytics.daily}>
                <defs>
                  <linearGradient id="appGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#7C6CF6" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#7C6CF6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#242938" vertical={false} />
                <XAxis dataKey="period" stroke="#5C6478" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#5C6478" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: "#161A23", border: "1px solid #242938", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "#9CA3B8" }}
                />
                <Area type="monotone" dataKey="applications" stroke="#7C6CF6" fill="url(#appGradient)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-sm text-ink-muted">
              No application activity yet — start applying to see trends here.
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top companies</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {analytics?.top_companies.length ? (
              analytics.top_companies.map((c) => (
                <div key={c.name} className="flex items-center justify-between text-sm py-1.5 border-b border-base-border/50 last:border-0">
                  <span className="text-ink-primary">{c.name}</span>
                  <span className="font-mono text-ink-secondary">{c.count}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-ink-muted">No applications yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top skills in your matches</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {analytics?.top_skills.length ? (
              analytics.top_skills.map((s) => (
                <span key={s.name} className="px-2.5 py-1 rounded-full bg-signal-violet/10 border border-signal-violet/20 text-signal-violet text-xs">
                  {s.name} <span className="text-ink-muted">· {s.count}</span>
                </span>
              ))
            ) : (
              <p className="text-sm text-ink-muted">No data yet.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
