"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Provider } from "@/lib/api";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [model, setModel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function refresh() {
    api.listProviders().then(setProviders).catch((e) => setError(e.message));
  }
  useEffect(refresh, []);

  async function test(id: number) {
    setNotice(null);
    setError(null);
    try {
      const r = await api.testProvider(id);
      if (r.ok) {
        setNotice(`Connection OK — ${r.models.length} models available.`);
        refresh();
      } else setError(r.error || "Connection failed.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test failed");
    }
  }

  async function add() {
    setNotice(null);
    setError(null);
    setBusy(true);
    try {
      const v = await api.validateProvider(apiKey);
      if (!v.ok) {
        setError(v.error || "Validation failed.");
        return;
      }
      setModels(v.models);
      const chosen = model || v.default_model || v.models[0];
      await api.saveProvider(apiKey, chosen);
      setNotice("Groq provider saved and set as active.");
      setApiKey("");
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save provider");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this provider and its stored key? Interview history is kept.")) return;
    await api.deleteProvider(id);
    refresh();
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <Link href="/dashboard" className="text-sm text-cyan-400">← Dashboard</Link>
      <h1 className="mt-2 text-2xl font-bold text-white">AI provider settings</h1>
      <p className="mt-1 text-sm text-slate-400">
        Keys are stored encrypted on the backend and shown masked only. Switching providers never deletes
        your interview history.
      </p>

      {error && <p className="mt-4 rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-300">{error}</p>}
      {notice && <p className="mt-4 rounded-lg border border-emerald-500/50 bg-emerald-500/10 p-3 text-sm text-emerald-300">{notice}</p>}

      <section className="mt-6 space-y-3">
        {providers.length === 0 && <p className="text-sm text-slate-400">No providers configured yet.</p>}
        {providers.map((p) => (
          <div key={p.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/80 p-4">
            <div>
              <p className="font-semibold text-white">
                {p.display_name} {p.is_active && <span className="ml-2 rounded-full bg-cyan-400/20 px-2 py-0.5 text-xs text-cyan-300">Active</span>}
              </p>
              <p className="text-sm text-slate-400">
                Key: {p.key_hint ?? "—"} · Model: {p.default_model ?? "—"} · Status: {p.validation_status}
              </p>
            </div>
            <div className="flex gap-2">
              <button className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm" onClick={() => test(p.id)}>Test</button>
              <button className="rounded-lg border border-red-500/50 px-3 py-1.5 text-sm text-red-300" onClick={() => remove(p.id)}>Delete</button>
            </div>
          </div>
        ))}
      </section>

      <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
        <h2 className="font-semibold text-white">Add / replace Groq</h2>
        <input
          className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-cyan-400"
          type="password"
          autoComplete="off"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value.trim())}
          placeholder="gsk_…"
        />
        {models.length > 0 && (
          <select className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2" value={model} onChange={(e) => setModel(e.target.value)}>
            {models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        )}
        <button
          className="mt-3 rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
          disabled={!apiKey || busy}
          onClick={add}
        >
          {busy ? "Validating…" : "Validate & save"}
        </button>
      </section>
    </main>
  );
}
