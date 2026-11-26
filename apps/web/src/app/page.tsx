import { redirect } from "next/navigation";
import { api } from "@/lib/api";

/** Root: send first-time users to onboarding, set-up users to the dashboard. */
export default async function Home() {
  try {
    const status = await api.onboardingStatus();
    redirect(status.setup_complete ? "/dashboard" : "/onboarding");
  } catch {
    // API unreachable — onboarding will surface the connection error.
    redirect("/onboarding");
  }
}
