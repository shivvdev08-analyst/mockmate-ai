"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError(null);
    setBusy(true);
    try {
      await api.login(pin);
      router.replace("/dashboard");
    } catch {
      setError("Incorrect PIN. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm rounded-2xl border border-slate-800 bg-slate-900/80 p-8">
        <h1 className="text-xl font-bold text-white">Sign in to MockMate AI</h1>
        <p className="mt-1 text-sm text-slate-400">Enter your owner PIN.</p>
        <input
          className="mt-6 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 outline-none focus:border-cyan-400"
          type="password"
          inputMode="numeric"
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 12))}
          placeholder="PIN"
          onKeyDown={(e) => e.key === "Enter" && pin.length >= 4 && submit()}
        />
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        <button
          className="mt-4 w-full rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
          disabled={pin.length < 4 || busy}
          onClick={submit}
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </div>
    </main>
  );
}
