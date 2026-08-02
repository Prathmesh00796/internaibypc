"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, MapPin, DollarSign, Bookmark, X, Send } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MatchScoreRing } from "@/components/match-score-ring";
import { api } from "@/lib/api-client";
import { Job } from "@/lib/types";

const SKILL_CHIPS = ["AI", "ML", "Python", "Java", "Web Development", "Software Developer"];

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [wfhOnly, setWfhOnly] = useState(false);
  const [freshersOnly, setFreshersOnly] = useState(false);
  const [minStipend, setMinStipend] = useState("");
  const [actionState, setActionState] = useState<Record<string, "loading" | "done">>({});

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/jobs", {
        params: {
          query: query || undefined,
          work_from_home: wfhOnly || undefined,
          freshers_only: freshersOnly || undefined,
          min_stipend: minStipend ? Number(minStipend) : undefined,
        },
      });
      setJobs(res.data);
    } catch {
      // handled by empty state
    } finally {
      setLoading(false);
    }
  }, [query, wfhOnly, freshersOnly, minStipend]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  async function handleAction(jobId: string, action: "apply" | "skip" | "save") {
    setActionState((prev) => ({ ...prev, [jobId]: "loading" }));
    try {
      await api.post(`/applications/${jobId}/action`, { action });
      setActionState((prev) => ({ ...prev, [jobId]: "done" }));
      setJobs((prev) => prev.filter((j) => j.id !== jobId || action === "save"));
    } catch {
      setActionState((prev) => {
        const next = { ...prev };
        delete next[jobId];
        return next;
      });
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-semibold">Find internships</h1>
        <p className="text-sm text-ink-secondary mt-1">Ranked by match to your profile.</p>
      </div>

      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchJobs()}
              placeholder="Search titles, e.g. 'Software Developer Intern'"
              className="w-full h-10 pl-9 pr-3 rounded-lg bg-base-elevated border border-base-border text-sm focus:border-signal-violet outline-none"
            />
          </div>
          <input
            value={minStipend}
            onChange={(e) => setMinStipend(e.target.value)}
            placeholder="Min stipend"
            type="number"
            className="w-32 h-10 px-3 rounded-lg bg-base-elevated border border-base-border text-sm focus:border-signal-violet outline-none"
          />
          <button
            onClick={() => setWfhOnly((v) => !v)}
            className={`h-10 px-4 rounded-lg text-sm font-medium border transition-colors ${
              wfhOnly ? "bg-signal-violet/10 border-signal-violet/40 text-signal-violet" : "bg-base-elevated border-base-border text-ink-secondary"
            }`}
          >
            Remote only
          </button>
          <button
            onClick={() => setFreshersOnly((v) => !v)}
            className={`h-10 px-4 rounded-lg text-sm font-medium border transition-colors ${
              freshersOnly ? "bg-signal-violet/10 border-signal-violet/40 text-signal-violet" : "bg-base-elevated border-base-border text-ink-secondary"
            }`}
          >
            Freshers
          </button>
          <Button onClick={fetchJobs} variant="primary">Search</Button>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {SKILL_CHIPS.map((skill) => (
            <button
              key={skill}
              onClick={() => setQuery(skill)}
              className="px-2.5 py-1 rounded-full bg-base-elevated border border-base-border text-xs text-ink-secondary hover:text-signal-violet hover:border-signal-violet/40 transition-colors"
            >
              {skill}
            </button>
          ))}
        </div>
      </Card>

      {loading ? (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-xl bg-base-elevated animate-pulse" />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-ink-secondary">No jobs match your filters right now.</p>
          <p className="text-sm text-ink-muted mt-1">
            New listings are pulled in automatically three times a day — check back soon.
          </p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job) => (
            <Card key={job.id} className="p-5 hover:border-signal-violet/30 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-display font-medium text-base">{job.title}</h3>
                    {!job.allows_auto_submit && (
                      <Badge variant="amber">Manual submit</Badge>
                    )}
                  </div>
                  <p className="text-sm text-ink-secondary mb-3">{job.company?.name || "Company"}</p>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-ink-muted mb-3">
                    <span className="flex items-center gap-1">
                      <MapPin size={13} /> {job.is_remote ? "Remote" : job.location || "Location TBD"}
                    </span>
                    {job.stipend_min && (
                      <span className="flex items-center gap-1">
                        <DollarSign size={13} /> {job.stipend_currency} {job.stipend_min.toLocaleString()}
                        {job.stipend_max ? `–${job.stipend_max.toLocaleString()}` : "+"}
                      </span>
                    )}
                    <Badge variant="neutral">{job.job_type.replace("_", " ")}</Badge>
                  </div>

                  {job.skills_required && job.skills_required.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {job.skills_required.slice(0, 6).map((skill) => (
                        <span key={skill} className="px-2 py-0.5 rounded-full bg-base-elevated border border-base-border text-xs text-ink-secondary">
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex flex-col items-center gap-3 shrink-0">
                  <MatchScoreRing score={job.match_score ?? 0} />
                  <div className="flex gap-1.5">
                    <Button
                      size="sm"
                      variant="success"
                      onClick={() => handleAction(job.id, "apply")}
                      disabled={actionState[job.id] === "loading"}
                      title="Apply"
                    >
                      <Send size={13} />
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleAction(job.id, "save")}
                      disabled={actionState[job.id] === "loading"}
                      title="Save"
                    >
                      <Bookmark size={13} />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleAction(job.id, "skip")}
                      disabled={actionState[job.id] === "loading"}
                      title="Skip"
                    >
                      <X size={13} />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
