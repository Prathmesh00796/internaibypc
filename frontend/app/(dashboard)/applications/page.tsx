"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import { Application, ApplicationStatus } from "@/lib/types";

const STATUS_CONFIG: Record<ApplicationStatus, { label: string; variant: "neutral" | "violet" | "teal" | "amber" | "coral" }> = {
  matched: { label: "Matched", variant: "neutral" },
  queued_for_review: { label: "In review queue", variant: "amber" },
  ready_to_submit: { label: "Ready to submit", variant: "amber" },
  saved: { label: "Saved", variant: "violet" },
  skipped: { label: "Skipped", variant: "neutral" },
  submitted: { label: "Submitted", variant: "violet" },
  failed: { label: "Failed", variant: "coral" },
  interview: { label: "Interview", variant: "teal" },
  offer: { label: "Offer", variant: "teal" },
  rejected: { label: "Rejected", variant: "coral" },
  withdrawn: { label: "Withdrawn", variant: "neutral" },
};

const FILTERS: { label: string; value: ApplicationStatus | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Submitted", value: "submitted" },
  { label: "Interview", value: "interview" },
  { label: "Offer", value: "offer" },
  { label: "Rejected", value: "rejected" },
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [filter, setFilter] = useState<ApplicationStatus | "all">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get("/applications", { params: filter !== "all" ? { status_filter: filter } : {} })
      .then((res) => setApplications(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-semibold">Applications</h1>
        <p className="text-sm text-ink-secondary mt-1">Every application you've prepared or sent.</p>
      </div>

      <div className="flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              filter === f.value
                ? "bg-signal-violet/10 border-signal-violet/40 text-signal-violet"
                : "bg-base-elevated border-base-border text-ink-secondary hover:text-ink-primary"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid gap-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-16 rounded-xl bg-base-elevated animate-pulse" />)}
        </div>
      ) : applications.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-ink-secondary">No applications in this view yet.</p>
        </Card>
      ) : (
        <div className="grid gap-3">
          {applications.map((app) => {
            const config = STATUS_CONFIG[app.status];
            return (
              <Card key={app.id} className="p-4 flex items-center justify-between">
                <div className="min-w-0">
                  <h3 className="font-medium text-sm truncate">{app.job?.title}</h3>
                  <p className="text-xs text-ink-secondary mt-0.5">{app.job?.company?.name}</p>
                </div>
                <div className="flex items-center gap-4 shrink-0">
                  {app.match_score != null && (
                    <span className="font-mono text-xs text-ink-muted">{Math.round(app.match_score)}% match</span>
                  )}
                  <Badge variant={config.variant}>{config.label}</Badge>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
