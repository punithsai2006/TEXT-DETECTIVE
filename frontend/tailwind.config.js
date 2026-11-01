/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        detective: {
          navy: "#0F172A",
          "navy-light": "#1E293B",
          "navy-dark": "#0A0F1D",
          gold: "#D97706",
          "gold-light": "#F59E0B",
          "gold-dark": "#B45309",
          cream: "#F8FAFC",
          parchment: "#F1F5F9",
          paper: "#F8FAFC",
          border: "#E2E8F0",
          muted: "#64748B",
          red: "#EF4444",
          green: "#10B981",
          blue: "#2563EB",
          indigo: "#4F46E5",
        },
      },
      fontFamily: {
        serif: ["Inter", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "Roboto", "sans-serif"],
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "Roboto", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "Consolas", "monospace"],
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)",
        card: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
        elevated: "0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04)",
      },
    },
  },
  plugins: [],
}
