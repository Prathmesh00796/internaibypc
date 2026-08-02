"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api-client";
import { AnalyticsOverview } from "@/lib/types";

const TABS = [
  { key: "daily", label: "Daily" },
  { key: "weekly", label: "Weekly" },
  { key: "monthly", label: "Monthly" },
] as const;

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("daily");

  useEffect(() => {
    api.get("/dashboard/analytics").then((res) => setData(res.data));
  }, []);

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-semibold">Analytics</h1>
        <p className="text-sm text-ink-secondary mt-1">How your search is performing over time.</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="p-5">
          <div className="text-xs text-ink-secondary mb-1">Response rate</div>
          <div className="stat-number text-3xl text-signal-violet">{data?.response_rate ?? 0}%</div>
        </Card>
        <Card className="p-5">
          <div className="text-xs text-ink-secondary mb-1">Interview rate</div>
          <div className="stat-number text-3xl text-signal-teal">{data?.interview_rate ?? 0}%</div>
        </Card>
        <Card className="p-5">
          <div className="text-xs text-ink-secondary mb-1">Offer rate</div>
          <div className="stat-number text-3xl text-signal-teal">{data?.offer_rate ?? 0}%</div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Activity breakdown</CardTitle>
          <div className="flex gap-1">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  tab === t.key ? "bg-signal-violet/10 text-signal-violet" : "text-ink-secondary hover:text-ink-primary"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </CardHeader>
        {data && data[tab].length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data[tab]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#242938" vertical={false} />
              <XAxis dataKey="period" stroke="#5C6478" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#5C6478" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "#161A23", border: "1px solid #242938", borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="applications" fill="#7C6CF6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="interviews" fill="#2DD4BF" radius={[4, 4, 0, 0]} />
              <Bar dataKey="offers" fill="#F5A524" radius={[4, 4, 0, 0]} />
              <Bar dataKey="rejections" fill="#F5657A" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[300px] flex items-center justify-center text-sm text-ink-muted">
            Not enough data yet for this view.
          </div>
        )}
      </Card>
    </div>
  );
}
