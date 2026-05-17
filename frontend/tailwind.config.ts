import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        muted: "hsl(var(--muted))",
        mutedForeground: "hsl(var(--muted-foreground))",
        card: "hsl(var(--card))",
        border: "hsl(var(--border))",
        primary: "hsl(var(--primary))",
        primaryForeground: "hsl(var(--primary-foreground))",
        accent: "hsl(var(--accent))",
        destructive: "hsl(var(--destructive))",
      },
      borderRadius: { lg: "0.75rem", md: "0.5rem", sm: "0.375rem" },
    },
  },
  plugins: [],
};
export default config;
