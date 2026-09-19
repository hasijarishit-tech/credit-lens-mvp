/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F6F4EF",
        surface: "#FFFFFF",
        surfacealt: "#EFEBE3",
        border: "#DEDAD0",
        ink: "#23282E",
        inkmuted: "#6B6560",
        accent: "#1F5C52",
        accentsoft: "#DCEAE6",
        good: "#3C8B5B",
        goodsoft: "#E4F1E8",
        warn: "#C97F1B",
        warnsoft: "#FBEDDA",
        critical: "#B5473C",
        criticalsoft: "#FAE6E3",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
}
