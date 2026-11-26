"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type OnboardingStatus, type Provider, type Usage } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .onboardingStatus()
      .then((s) => {
        setStatus(s);
        if (!s.setup_complete) router.replace("/onboarding");
      })
      .catch(() => setError("Could not reach the API server. Start the backend on port 8000."));
    api.listProviders().then(setProviders).catch(() => {});
    api.usage().then(setUsage).catch(() => {});
  }, [router]);

  const active = providers.find((p) => p.is_active);

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold tracking-widest text-cyan-400">MOCKMATE AI</p>
          <h1 className="mt-1 text-3xl font-bold text-white">Welcome back</h1>
          <p className="mt-1 text-sm text-slate-400">Practice smarter. Interview stronger.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/settings/providers" className="rounded-lg border border-slate-700 px-4 py-2 text-sm hover:border-slate-500">
            Provider settings
          </Link>
          <Link href="/login" className="rounded-lg border border-slate-700 px-4 py-2 text-sm hover:border-slate-500">
            Sign out
          </Link>
        </div>
      </header>

      {error && <p className="mt-6 rounded-lg border border-amber-500/50 bg-amber-500/10 p-3 text-sm text-amber-200">{error}</p>}

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <h2 className="font-semibold text-white">Start an interview</h2>
          <p className="mt-1 text-sm text-slate-400">Text interviews arrive in Phase 3. For now, your setup is ready.</p>
          <button disabled className="mt-4 cursor-not-allowed rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-slate-400">
            Start interview — coming in Phase 3
          </button>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <h2 className="font-semibold text-white">AI provider</h2>
          {active ? (
            <p className="mt-2 text-sm text-slate-300">
              {active.display_name} · <span className="text-emerald-400">● connected</span>
              <br />
              <span className="text-slate-400">Key: {active.key_hint ?? "—"}</span>
              <br />
              <span className="text-slate-400">Model: {active.default_model ?? "—"}</span>
            </p>
          ) : (
            <p className="mt-2 text-sm text-amber-300">No active provider — finish onboarding first.</p>
          )}
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <h2 className="font-semibold text-white">Usage</h2>
          <p className="mt-2 text-sm text-slate-300">
            LLM calls: {usage?.calls ?? 0}
            <br />
            Tokens used: {usage?.total_tokens ?? 0}
            <br />
            Estimated cost: ${usage?.estimated_cost_usd.toFixed(4) ?? "0.0000"}
          </p>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
        <h2 className="font-semibold text-white">Recent sessions</h2>
        <p className="mt-2 text-sm text-slate-400">
          No interviews yet. Once Phase 3 lands, your sessions, scores and reports will appear here.
        </p>
        <div className="mt-4 grid gap-2 text-sm text-slate-500 sm:grid-cols-3">
          <span>Total interviews: 0</span>
          <span>Average score: —</span>
          <span>Weakest competencies: —</span>
        </div>
      </section>

      {status && (
        <p className="mt-6 text-xs text-slate-500">
          Setup: PIN {status.pin_set ? "✓" : "✗"} · Provider {status.provider_configured ? "✓" : "✗"} · Profile{" "}
          {status.profile_completed ? "✓" : "✗"}
        </p>
      )}
    </main>
  );
}
