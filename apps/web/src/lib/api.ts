/** All API calls go to the FastAPI backend. No API keys are stored here,
 * in localStorage, or in logs — the browser only ever sends the PIN/session
 * cookie and the Groq key once, in the validate/save request body. */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface OnboardingStatus {
  setup_complete: boolean;
  pin_set: boolean;
  provider_configured: boolean;
  profile_completed: boolean;
  onboarding_completed: boolean;
}

export interface Provider {
  id: number;
  name: string;
  display_name: string;
  base_url: string | null;
  is_active: boolean;
  is_enabled: boolean;
  default_model: string | null;
  task_models: Record<string, string>;
  key_hint: string | null;
  validation_status: string;
  last_validated_at: string | null;
}

export interface Usage {
  total_tokens: number;
  estimated_cost_usd: number;
  calls: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  if (!res.ok) {
    const detail =
      (data as { detail?: string } | null)?.detail || `Request failed (${res.status})`;
    throw new Error(typeof detail === "string" ? detail : `Request failed (${res.status})`);
  }
  return data as T;
}

export const api = {
  health: () => request<{ ok: boolean }>("/health"),
  onboardingStatus: () => request<OnboardingStatus>("/api/v1/onboarding/status"),
  setupPin: (pin: string) =>
    request<{ ok: boolean }>("/api/v1/auth/setup-pin", {
      method: "POST",
      body: JSON.stringify({ pin }),
    }),
  login: (pin: string) =>
    request<{ ok: boolean }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ pin }),
    }),
  logout: () =>
    request<{ ok: boolean }>("/api/v1/auth/logout", { method: "POST" }),
  me: () => request<{ ok: boolean; user_id: number }>("/api/v1/auth/me"),
  validateProvider: (apiKey: string) =>
    request<{ ok: boolean; models: string[]; default_model?: string; error?: string; error_code?: string }>(
      "/api/v1/providers/validate",
      { method: "POST", body: JSON.stringify({ provider: "groq", api_key: apiKey }) },
    ),
  saveProvider: (apiKey: string, defaultModel?: string) =>
    request<Provider>("/api/v1/providers", {
      method: "POST",
      body: JSON.stringify({ provider: "groq", api_key: apiKey, default_model: defaultModel }),
    }),
  listProviders: () => request<Provider[]>("/api/v1/providers"),
  testProvider: (id: number) =>
    request<{ ok: boolean; models: string[]; error?: string }>("/api/v1/providers/" + id + "/test", {
      method: "POST",
    }),
  deleteProvider: (id: number) =>
    request<{ ok: boolean }>("/api/v1/providers/" + id, { method: "DELETE" }),
  usage: () => request<Usage>("/api/v1/providers/usage"),
  saveProfile: (profile: {
    full_name?: string;
    target_roles: string[];
    experience_level?: string;
    target_companies?: string;
  }) =>
    request<{ ok: boolean }>("/api/v1/onboarding/profile", {
      method: "POST",
      body: JSON.stringify(profile),
    }),
};
