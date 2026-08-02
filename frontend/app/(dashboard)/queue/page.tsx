"use client";

import { useEffect, useState } from "react";
import { ExternalLink, CheckCircle2, FileText, RefreshCw } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MatchScoreRing } from "@/components/match-score-ring";
import { api } from "@/lib/api-client";
import { Application } from "@/lib/types";

export default function QueuePage() {
  const [queue, setQueue] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [regenerating, setRegenerating] = useState<string | null>(null);

  async function fetchQueue() {
    setLoading(true);
    try {
      const res = await api.get("/applications/queue");
      setQueue(res.data);
    } catch {
      // empty state handles this
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchQueue();
  }, []);

  async function handleConfirm(applicationId: string) {
    setSubmitting(applicationId);
    try {
      await api.post(`/applications/${applicationId}/confirm-submit`, { confirmed: true });
      setQueue((prev) => prev.filter((a) => a.id !== applicationId));
    } finally {
      setSubmitting(null);
    }
  }

  async function handleRegenerate(applicationId: string) {
    setRegenerating(applicationId);
    try {
      const res = await api.post(`/applications/${applicationId}/regenerate-cover-letter`);
      setQueue((prev) => prev.map((a) => (a.id === applicationId ? res.data : a)));
    } finally {
      setRegenerating(null);
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-semibold">Review queue</h1>
        <p className="text-sm text-ink-secondary mt-1">
          Applications are prepared but never sent automatically — review each one and confirm.
        </p>
      </div>

      {loading ? (
        <div className="grid gap-4">
          {[1, 2].map((i) => <div key={i} className="h-24 rounded-xl bg-base-elevated animate-pulse" />)}
        </div>
      ) : queue.length === 0 ? (
        <Card className="p-12 text-center">
          <CheckCircle2 size={32} className="mx-auto text-signal-teal mb-3" />
          <p className="text-ink-secondary">Your queue is empty.</p>
          <p className="text-sm text-ink-muted mt-1">Applications you prepare from Find Jobs will show up here.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {queue.map((app) => {
            const isExpanded = expandedId === app.id;
            return (
              <Card key={app.id} className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-display font-medium">{app.job?.title}</h3>
                      {app.requires_manual_submission ? (
                        <Badge variant="amber">Needs your submission on {app.job?.source}</Badge>
                      ) : (
                        <Badge variant="teal">Auto-submit eligible</Badge>
                      )}
                    </div>
                    <p className="text-sm text-ink-secondary mb-3">{app.job?.company?.name}</p>

                    <button
                      onClick={() => setExpandedId(isExpanded ? null : app.id)}
                      className="text-xs text-signal-violet hover:underline flex items-center gap-1"
                    >
                      <FileText size={12} />
                      {isExpanded ? "Hide" : "Review"} cover letter & autofill data
                    </button>

                    {isExpanded && (
                      <div className="mt-4 space-y-3">
                        <div className="bg-base-elevated border border-base-border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-ink-secondary uppercase tracking-wider">Cover letter</span>
                            <button
                              onClick={() => handleRegenerate(app.id)}
                              disabled={regenerating === app.id}
                              className="text-xs text-signal-violet hover:underline flex items-center gap-1"
                            >
                              <RefreshCw size={11} className={regenerating === app.id ? "animate-spin" : ""} />
                              Regenerate
                            </button>
                          </div>
                          <p className="text-sm text-ink-secondary whitespace-pre-line leading-relaxed">
                            {app.cover_letter_text}
                          </p>
                        </div>

                        {app.autofill_payload && (
                          <div className="bg-base-elevated border border-base-border rounded-lg p-4">
                            <span className="text-xs font-medium text-ink-secondary uppercase tracking-wider mb-2 block">
                              Autofill data
                            </span>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              {Object.entries(app.autofill_payload)
                                .filter(([, v]) => v)
                                .map(([key, value]) => (
                                  <div key={key}>
                                    <span className="text-ink-muted">{key.replace(/_/g, " ")}: </span>
                                    <span className="text-ink-primary">
                                      {Array.isArray(value) ? value.join(", ") : String(value)}
                                    </span>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}

                        {app.requires_manual_submission && app.job?.external_url && (
                          <a
                            href={app.job.external_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs text-signal-violet hover:underline"
                          >
                            Open application on {app.job.source} <ExternalLink size={11} />
                          </a>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col items-center gap-3 shrink-0">
                    <MatchScoreRing score={app.match_score ?? 0} size={48} />
                    <Button
                      size="sm"
                      variant="success"
                      onClick={() => handleConfirm(app.id)}
                      disabled={submitting === app.id}
                    >
                      {submitting === app.id ? "..." : "Confirm & submit"}
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
