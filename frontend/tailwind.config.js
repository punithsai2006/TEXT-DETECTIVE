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
          navy: "#131A2E",
          "navy-light": "#1D2744",
          "navy-dark": "#0B101D",
          gold: "#C9962F",
          "gold-light": "#E0B354",
          "gold-dark": "#A87A1E",
          cream: "#F4F0E6",
          parchment: "#FDFBF7",
          paper: "#FAF7EF",
          border: "#E2DDD0",
          muted: "#7A7264",
          red: "#B93838",
          green: "#2E7D4F",
        },
      },
      fontFamily: {
        serif: ["Georgia", "Cambria", "'Times New Roman'", "serif"],
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "'Segoe UI'", "Roboto", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
}
