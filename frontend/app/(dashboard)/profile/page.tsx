"use client";

import { useEffect, useState, useRef } from "react";
import { Upload, Loader2, Check, Download, X } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import { Profile, Resume } from "@/lib/types";

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saved, setSaved] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function loadData() {
    const [profileRes, resumesRes] = await Promise.all([api.get("/profile"), api.get("/resumes")]);
    setProfile(profileRes.data);
    setResumes(resumesRes.data);
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      await api.post("/resumes/upload", formData, { headers: { "Content-Type": "multipart/form-data" } });
      // Poll briefly for parse completion, then reload profile (auto-filled fields)
      setTimeout(loadData, 3000);
      await loadData();
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    try {
      const { skills, projects, experiences, id, active_resume_id, ...updateFields } = profile;
      await api.put("/profile", updateFields);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerateResume(template: "classic" | "modern") {
    const res = await api.post(`/resumes/generate?template=${template}`, null, { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = `resume_${template}.pdf`;
    link.click();
  }

  function updateField<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  if (!profile) {
    return <div className="h-64 flex items-center justify-center"><Loader2 className="animate-spin text-signal-violet" /></div>;
  }

  return (
    <div className="space-y-6 animate-fade-up max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">Profile</h1>
          <p className="text-sm text-ink-secondary mt-1">Powers your match score and autofill.</p>
        </div>
        <Button onClick={handleSave} disabled={saving} variant="primary">
          {saving ? <Loader2 size={15} className="animate-spin" /> : saved ? <Check size={15} /> : "Save changes"}
        </Button>
      </div>

      <Card>
        <CardHeader><CardTitle>Resume</CardTitle></CardHeader>
        <div className="space-y-3">
          <input ref={fileInputRef} type="file" accept="application/pdf" onChange={handleUpload} className="hidden" id="resume-upload" />
          <label
            htmlFor="resume-upload"
            className="flex items-center justify-center gap-2 h-24 rounded-lg border-2 border-dashed border-base-border hover:border-signal-violet/40 cursor-pointer text-sm text-ink-secondary transition-colors"
          >
            {uploading ? (
              <><Loader2 size={16} className="animate-spin" /> Uploading & parsing...</>
            ) : (
              <><Upload size={16} /> Upload PDF resume — we&apos;ll auto-fill your profile</>
            )}
          </label>

          {resumes.length > 0 && (
            <div className="space-y-2">
              {resumes.map((r) => (
                <div key={r.id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-base-elevated border border-base-border text-sm">
                  <span className="truncate">{r.file_name}</span>
                  <Badge variant={r.parse_status === "completed" ? "teal" : r.parse_status === "failed" ? "coral" : "amber"}>
                    {r.parse_status}
                  </Badge>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <Button size="sm" variant="secondary" onClick={() => handleGenerateResume("classic")}>
              <Download size={13} /> Generate resume (Classic)
            </Button>
            <Button size="sm" variant="secondary" onClick={() => handleGenerateResume("modern")}>
              <Download size={13} /> Generate resume (Modern)
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Basic information</CardTitle></CardHeader>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Full name" value={profile.full_name} onChange={(v) => updateField("full_name", v)} />
          <Field label="Phone" value={profile.phone} onChange={(v) => updateField("phone", v)} />
          <Field label="Location" value={profile.location} onChange={(v) => updateField("location", v)} />
          <Field label="College" value={profile.college} onChange={(v) => updateField("college", v)} />
          <Field label="Degree" value={profile.degree} onChange={(v) => updateField("degree", v)} />
          <Field
            label="Graduation year"
            value={profile.graduation_year?.toString() ?? ""}
            onChange={(v) => updateField("graduation_year", v ? Number(v) : null)}
            type="number"
          />
          <Field
            label="CGPA"
            value={profile.cgpa?.toString() ?? ""}
            onChange={(v) => updateField("cgpa", v ? Number(v) : null)}
            type="number"
          />
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Links</CardTitle></CardHeader>
        <div className="grid grid-cols-1 gap-4">
          <Field label="LinkedIn" value={profile.linkedin_url} onChange={(v) => updateField("linkedin_url", v)} />
          <Field label="GitHub" value={profile.github_url} onChange={(v) => updateField("github_url", v)} />
          <Field label="Portfolio" value={profile.portfolio_url} onChange={(v) => updateField("portfolio_url", v)} />
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Preferences</CardTitle></CardHeader>
        <div className="grid grid-cols-2 gap-4">
          <Field
            label="Preferred stipend (min)"
            value={profile.preferred_stipend_min?.toString() ?? ""}
            onChange={(v) => updateField("preferred_stipend_min", v ? Number(v) : null)}
            type="number"
          />
          <div>
            <label className="text-xs font-medium text-ink-secondary mb-1.5 block">Job type</label>
            <select
              value={profile.preferred_job_type ?? ""}
              onChange={(e) => updateField("preferred_job_type", e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-base-elevated border border-base-border text-sm outline-none focus:border-signal-violet"
            >
              <option value="">Any</option>
              <option value="internship">Internship</option>
              <option value="full_time">Full-time</option>
            </select>
          </div>
        </div>
        <div className="flex gap-4 mt-4">
          <label className="flex items-center gap-2 text-sm text-ink-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={profile.work_from_home_only}
              onChange={(e) => updateField("work_from_home_only", e.target.checked)}
              className="accent-signal-violet"
            />
            Remote only
          </label>
          <label className="flex items-center gap-2 text-sm text-ink-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={profile.fresher_only}
              onChange={(e) => updateField("fresher_only", e.target.checked)}
              className="accent-signal-violet"
            />
            Freshers only
          </label>
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Skills</CardTitle></CardHeader>
        <div className="flex flex-wrap gap-2">
          {profile.skills.map((skill) => (
            <span key={skill.id} className="px-2.5 py-1 rounded-full bg-base-elevated border border-base-border text-xs flex items-center gap-1.5">
              {skill.name}
              {skill.source === "resume_parsed" && <span className="text-signal-teal text-[10px]">●</span>}
            </span>
          ))}
          {profile.skills.length === 0 && (
            <p className="text-sm text-ink-muted">No skills yet — upload a resume or add manually.</p>
          )}
        </div>
      </Card>
    </div>
  );
}

function Field({
  label, value, onChange, type = "text",
}: {
  label: string;
  value: string | null | undefined;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-ink-secondary mb-1.5 block">{label}</label>
      <input
        type={type}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-10 px-3 rounded-lg bg-base-elevated border border-base-border text-sm outline-none focus:border-signal-violet transition-colors"
      />
    </div>
  );
}
