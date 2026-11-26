import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MockMate AI — Practice smarter. Interview stronger.",
  description: "Personal-first AI interview intelligence platform.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#070b14] text-slate-200 antialiased">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(60rem_30rem_at_50%_-10%,rgba(34,211,238,0.12),transparent),radial-gradient(40rem_25rem_at_90%_0%,rgba(139,92,246,0.12),transparent)]" />
        <div className="relative">{children}</div>
      </body>
    </html>
  );
}
