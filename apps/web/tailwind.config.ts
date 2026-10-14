import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      gridTemplateColumns: {
        "13": "repeat(13, minmax(0, 1fr))",
      },
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        felt: {
          50: "#ecfdf5",
          100: "#d1fae5",
          500: "#10b981",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
        },
      },
    },
  },
  plugins: [],
};

export default config;
