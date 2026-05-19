import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          950: "#020d04",
          900: "#061209",
          850: "#0a1a0d",
          800: "#112214",
          750: "#192d1c",
          700: "#213824",
          600: "#2d5230",
          500: "#3d6b42",
          400: "#518a56",
          300: "#6aab70",
          200: "#90cc95",
          100: "#c5e8c7",
          50:  "#edf7ee",
        },
      },
      fontFamily: {
        sans: ["var(--font-noto)", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.4s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
