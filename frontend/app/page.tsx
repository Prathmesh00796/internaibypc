import Link from "next/link";
import { Sparkles, ArrowRight, Zap, Target, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen bg-base overflow-hidden">
      <header className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-signal-violet/20 border border-signal-violet/40 flex items-center justify-center">
            <Sparkles size={16} className="text-signal-violet" />
          </div>
          <span className="font-display font-semibold text-lg">InternAI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Log in</Button>
          </Link>
          <Link href="/register">
            <Button variant="primary" size="sm">Get started</Button>
          </Link>
        </div>
      </header>

      <section className="max-w-4xl mx-auto px-6 pt-20 pb-24 text-center animate-fade-up">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-base-border bg-base-elevated/60 text-xs text-ink-secondary mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-signal-teal animate-pulse" />
          Scanning for new internships, three times a day
        </div>
        <h1 className="font-display text-5xl md:text-6xl font-semibold tracking-tight leading-[1.05] mb-6">
          Stop refreshing job boards.
          <br />
          <span className="text-signal-violet">Let the search find you.</span>
        </h1>
        <p className="text-ink-secondary text-lg max-w-xl mx-auto mb-10">
          InternAI parses your resume, scores every internship against your profile,
          and prepares your application — you just review and confirm.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link href="/register">
            <Button size="lg" variant="primary">
              Create your profile <ArrowRight size={16} />
            </Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="secondary">I have an account</Button>
          </Link>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 pb-24 grid grid-cols-1 md:grid-cols-3 gap-5">
        {[
          {
            icon: Target,
            title: "Match scoring, not guesswork",
            body: "Every listing is scored 0–100 against your skills, CGPA, grad year, location, and resume — so you know exactly why it's a fit.",
          },
          {
            icon: Zap,
            title: "Applications, pre-filled",
            body: "Your details and a personalized cover letter are ready before you even open the listing. You just confirm and send.",
          },
          {
            icon: ShieldCheck,
            title: "You're always in control",
            body: "Nothing gets submitted without your review. InternAI prepares; you decide what goes out.",
          },
        ].map((f) => (
          <div key={f.title} className="glass-card p-6">
            <f.icon size={20} className="text-signal-violet mb-4" />
            <h3 className="font-display font-medium mb-2">{f.title}</h3>
            <p className="text-sm text-ink-secondary leading-relaxed">{f.body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
