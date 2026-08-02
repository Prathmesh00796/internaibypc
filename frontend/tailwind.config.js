/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: {
          DEFAULT: "#0B0D12",
          elevated: "#12151C",
          panel: "#161A23",
          border: "#242938",
        },
        signal: {
          violet: "#7C6CF6",
          "violet-dim": "#5B4FCB",
          teal: "#2DD4BF",
          amber: "#F5A524",
          coral: "#F5657A",
        },
        ink: {
          primary: "#EDEFF5",
          secondary: "#9CA3B8",
          muted: "#5C6478",
        },
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      backdropBlur: {
        xs: "2px",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(124,108,246,0.15), 0 8px 32px -8px rgba(124,108,246,0.25)",
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "ring-fill": {
          "0%": { strokeDashoffset: "var(--ring-start)" },
          "100%": { strokeDashoffset: "var(--ring-end)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out both",
        "ring-fill": "ring-fill 1s cubic-bezier(0.4, 0, 0.2, 1) forwards",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
};
