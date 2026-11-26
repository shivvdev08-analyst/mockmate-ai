import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0a0e1a",
        panel: "#111827",
        accent: "#22d3ee",
        violet2: "#8b5cf6",
      },
    },
  },
  plugins: [],
};
export default config;
