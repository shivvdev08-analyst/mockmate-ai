"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const ROLES = ["AI Engineer", "Machine Learning Engineer", "Data Scientist", "Full-Stack AI Product Engineer"];

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur">
      {children}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-300">{label}</span>
      {children}
    </label>
  );
}

const inputCls =
  "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-cyan-400";
const btnPrimary =
  "rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-300 disabled:opacity-50";
const btnGhost =
  "rounded-lg border border-slate-700 px-4 py-2 text-slate-200 hover:border-slate-500 disabled:opacity-50";

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [pin, setPin] = useState("");
  const [pinSet, setPinSet] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [model, setModel] = useState("");
  const [validated, setValidated] = useState(false);
  const [savedHint, setSavedHint] = useState<string | null>(null);
  const [fullName, setFullName] = useState("");
  const [roles, setRoles] = useState<string[]>(["AI Engineer"]);
  const [experience, setExperience] = useState("Fresher / Student");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [apiDown, setApiDown] = useState(false);

  useEffect(() => {
    api
      .onboardingStatus()
      .then((s) => {
        setPinSet(s.pin_set);
        if (s.setup_complete) router.replace("/dashboard");
        else if (s.pin_set && s.provider_configured) setStep(2);
        else if (s.pin_set) setStep(1);
      })
      .catch(() => setApiDown(true));
  }, [router]);

  async function handlePin() {
    setError(null);
    setBusy(true);
    try {
      await api.setupPin(pin);
      setPinSet(true);
      setStep(1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not set PIN");
    } finally {
      setBusy(false);
    }
  }

  async function handleTest() {
    setError(null);
    setValidated(false);
    setBusy(true);
    try {
      const res = await api.validateProvider(apiKey);
      if (!res.ok) {
        setError(res.error || "Connection failed. Check the key and try again.");
        return;
      }
      setModels(res.models);
      setModel(res.default_model || res.models[0] || "");
      setValidated(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reach the API server");
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveProvider() {
    setError(null);
    setBusy(true);
    try {
      const saved = await api.saveProvider(apiKey, model || undefined);
      setSavedHint(saved.key_hint);
      setStep(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save provider");
    } finally {
      setBusy(false);
    }
  }

  async function handleProfile() {
    setError(null);
    setBusy(true);
    try {
      await api.saveProfile({ full_name: fullName, target_roles: roles, experience_level: experience });
      router.replace("/dashboard");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save profile");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-xl">
        <div className="mb-6 text-center">
          <p className="text-sm font-semibold tracking-widest text-cyan-400">MOCKMATE AI</p>
          <h1 className="mt-1 text-3xl font-bold text-white">Practice smarter. Interview stronger.</h1>
        </div>
        {apiDown && (
          <p className="mb-4 rounded-lg border border-amber-500/50 bg-amber-500/10 p-3 text-sm text-amber-200">
            Could not reach the API server. Start the backend first: <code>uvicorn app.main:app --port 8000</code>{" "}
            in <code>apps/api</code>.
          </p>
        )}
        <div className="mb-4 flex gap-2 text-xs">
          {["Welcome", "Groq setup", "Profile"].map((label, i) => (
            <span
              key={label}
              className={`flex-1 rounded-full px-2 py-1 text-center ${
                i <= step ? "bg-cyan-400/20 text-cyan-300" : "bg-slate-800 text-slate-500"
              }`}
            >
              {i + 1}. {label}
            </span>
          ))}
        </div>

        {step === 0 && (
          <Card>
            <h2 className="text-xl font-semibold text-white">Welcome to MockMate AI</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              Your personal AI interviewer: it reads your resume and a job description, runs realistic
              interviews, and tracks how you improve over time. Everything is private to you first —
              no billing, no public launch, just practice.
            </p>
            <ul className="mt-4 space-y-2 text-sm text-slate-300">
              <li>• Realistic HR, technical and behavioural interviews</li>
              <li>• Questions based on your actual resume and target role</li>
              <li>• Communication feedback and a report after every session</li>
            </ul>
            {!pinSet ? (
              <div className="mt-6 space-y-3">
                <Field label="Create a 4–12 digit owner PIN (protects this device's setup)">
                  <input
                    className={inputCls}
                    type="password"
                    inputMode="numeric"
                    value={pin}
                    onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 12))}
                    placeholder="e.g. 1234"
                  />
                </Field>
                <button className={btnPrimary} disabled={pin.length < 4 || busy} onClick={handlePin}>
                  {busy ? "Setting PIN…" : "Set PIN & continue"}
                </button>
              </div>
            ) : (
              <button className={`${btnPrimary} mt-6`} onClick={() => setStep(1)}>
                Continue to Groq setup →
              </button>
            )}
          </Card>
        )}

        {step === 1 && (
          <Card>
            <h2 className="text-xl font-semibold text-white">Connect Groq</h2>
            <p className="mt-2 text-sm text-slate-400">
              Groq is your first LLM provider. Paste your key below — it is sent only to your own backend,
              encrypted there, and never shown in full again. Get a free key at console.groq.com.
            </p>
            <div className="mt-6 space-y-4">
              <Field label="Groq API key">
                <input
                  className={inputCls}
                  type="password"
                  autoComplete="off"
                  value={apiKey}
                  onChange={(e) => {
                    setApiKey(e.target.value.trim());
                    setValidated(false);
                  }}
                  placeholder="gsk_…"
                />
              </Field>
              <div className="flex gap-2">
                <button className={btnGhost} disabled={!apiKey || busy} onClick={handleTest}>
                  {busy ? "Testing…" : "Test connection"}
                </button>
              </div>
              {validated && (
                <p className="rounded-lg border border-emerald-500/50 bg-emerald-500/10 p-3 text-sm text-emerald-300">
                  ✓ Connected to Groq. {models.length} model{models.length === 1 ? "" : "s"} available.
                </p>
              )}
              {models.length > 0 && (
                <Field label="Model">
                  <select className={inputCls} value={model} onChange={(e) => setModel(e.target.value)}>
                    {models.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
              {savedHint && <p className="text-sm text-slate-400">Saved key: <code>{savedHint}</code></p>}
              <button className={btnPrimary} disabled={!validated || busy} onClick={handleSaveProvider}>
                Save Groq & continue →
              </button>
              <p className="text-xs text-slate-500">
                The model list comes from a live Groq response — no model is hard-coded, so if Groq changes
                its catalogue this list changes with it.
              </p>
            </div>
          </Card>
        )}

        {step === 2 && (
          <Card>
            <h2 className="text-xl font-semibold text-white">Your interview profile</h2>
            <p className="mt-2 text-sm text-slate-400">This shapes the questions MockMate asks you.</p>
            <div className="mt-6 space-y-4">
              <Field label="Full name">
                <input className={inputCls} value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Shivam Vinod Chaudhari" />
              </Field>
              <Field label="Target roles">
                <div className="flex flex-wrap gap-2">
                  {ROLES.map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setRoles(roles.includes(r) ? roles.filter((x) => x !== r) : [...roles, r])}
                      className={`rounded-full border px-3 py-1 text-sm ${
                        roles.includes(r) ? "border-cyan-400 bg-cyan-400/20 text-cyan-200" : "border-slate-700 text-slate-400"
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Experience level">
                <select className={inputCls} value={experience} onChange={(e) => setExperience(e.target.value)}>
                  <option>Fresher / Student</option>
                  <option>0–1 years</option>
                  <option>1–3 years</option>
                  <option>3+ years</option>
                </select>
              </Field>
              <button className={btnPrimary} disabled={busy} onClick={handleProfile}>
                {busy ? "Saving…" : "Finish setup → Dashboard"}
              </button>
            </div>
          </Card>
        )}

        {error && <p className="mt-4 rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-300">{error}</p>}
      </div>
    </main>
  );
}
