/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#f5f6f7",
          900: "#ffffff",
          850: "#f9fafb",
          800: "#f3f4f6",
          700: "#e5e7eb",
          600: "#d1d5db",
          500: "#9ca3af",
        },
        ink: {
          DEFAULT: "#111827",
          dim: "#4b5563",
          faint: "#9ca3af",
        },
        line: {
          DEFAULT: "#e5e7eb",
          soft: "#f3f4f6",
          strong: "#d1d5db",
        },
        atmos: {
          50: "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fb923c",
          400: "#f97316",
          500: "#ea580c",
          600: "#c2410c",
          glow: "rgba(249,115,22,0.12)",
        },
        meteo: {
          temp: "#dc2626",
          pressure: "#2563eb",
          humidity: "#0891b2",
          wind: "#16a34a",
          rain: "#7c3aed",
          solar: "#d97706",
          battery: "#16a34a",
        },
        signal: {
          good: "#16a34a",
          warn: "#d97706",
          bad: "#dc2626",
          info: "#2563eb",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 3px 0 rgba(0,0,0,0.07), 0 1px 2px -1px rgba(0,0,0,0.05)",
        card: "0 2px 8px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.04)",
        glow: "0 0 0 3px rgba(249,115,22,0.15)",
      },
      backgroundImage: {
        grid: "none",
      },
      keyframes: {
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
        rise: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        drift: {
          "0%": { transform: "translate(0,0)" },
          "50%": { transform: "translate(4px,-4px)" },
          "100%": { transform: "translate(0,0)" },
        },
      },
      animation: {
        pulseSoft: "pulseSoft 2s ease-in-out infinite",
        rise: "rise 0.4s ease-out both",
        marquee: "marquee 30s linear infinite",
        scan: "scan 6s linear infinite",
        drift: "drift 9s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#f1f6fc", // daylight atmospheric sky base
          900: "#ffffff", // clean cloud-white card/panel surface
          850: "#f8fafc", // elevated panel header / subtle contrast
          800: "#edf2f7", // soft pills and secondary button surface
          700: "#e2e8f0", // light borders and dividers
          600: "#cbd5e1", // crisp card borders
          500: "#94a3b8", // muted border lines
        },
        line: {
          DEFAULT: "rgba(148, 163, 184, 0.28)", // soft slate border
          soft: "rgba(148, 163, 184, 0.16)",
          strong: "rgba(148, 163, 184, 0.45)",
        },
        ink: {
          DEFAULT: "#0f172a", // crisp slate-900 text
          dim: "#475569",    // readable slate-600 subtext
          faint: "#64748b",  // muted slate-500 labels
        },
        atmos: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0284c7",
          600: "#0369a1",
          glow: "rgba(2, 132, 199, 0.15)",
        },
        meteo: {
          temp: "#ea580c",     // warm solar amber
          pressure: "#0284c7", // clear atmospheric blue
          humidity: "#0891b2", // water vapor cyan
          wind: "#16a34a",     // fresh breeze green
          rain: "#4f46e5",     // precipitation indigo
          solar: "#d97706",    // sunshine gold
          battery: "#16a34a",  // healthy battery green
        },
        signal: {
          good: "#16a34a",
          warn: "#d97706",
          bad: "#dc2626",
          info: "#0284c7",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)",
        card: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
        glow: "0 0 24px -4px rgba(2, 132, 199, 0.18)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(148,163,184,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.08) 1px, transparent 1px)",
      },
      keyframes: {
        pulseSoft: {
          "0%, 100%": { opacity: 1, transform: "scale(1)" },
          "50%": { opacity: 0.7, transform: "scale(1.08)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        drift: {
          "0%": { transform: "translate(0,0)" },
          "50%": { transform: "translate(6px,-6px)" },
          "100%": { transform: "translate(0,0)" },
        },
        rise: {
          "0%": { opacity: 0, transform: "translateY(10px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      animation: {
        pulseSoft: "pulseSoft 2.4s ease-in-out infinite",
        scan: "scan 6s linear infinite",
        drift: "drift 9s ease-in-out infinite",
        rise: "rise 0.6s ease-out both",
        marquee: "marquee 30s linear infinite",
      },
    },
  },
  plugins: [],
};
