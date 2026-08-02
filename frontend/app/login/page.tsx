"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, setAuthTokens } from "@/lib/api-client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.post("/auth/login", { email, password });
      setAuthTokens(res.data.access_token, res.data.refresh_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <div className="w-8 h-8 rounded-lg bg-signal-violet/20 border border-signal-violet/40 flex items-center justify-center">
            <Sparkles size={16} className="text-signal-violet" />
          </div>
          <span className="font-display font-semibold text-lg">InternAI</span>
        </div>

        <div className="glass-panel p-8">
          <h1 className="font-display text-xl font-semibold mb-1">Welcome back</h1>
          <p className="text-sm text-ink-secondary mb-6">Log in to keep your search running.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-ink-secondary mb-1.5 block">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-10 px-3 rounded-lg bg-base-elevated border border-base-border text-sm focus:border-signal-violet outline-none transition-colors"
                placeholder="you@university.edu"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-ink-secondary mb-1.5 block">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-10 px-3 rounded-lg bg-base-elevated border border-base-border text-sm focus:border-signal-violet outline-none transition-colors"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="text-xs text-signal-coral bg-signal-coral/10 border border-signal-coral/30 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <Button type="submit" variant="primary" className="w-full" disabled={loading}>
              {loading ? <Loader2 size={16} className="animate-spin" /> : "Log in"}
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-ink-secondary mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-signal-violet hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
