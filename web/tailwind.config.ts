import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0d12",
        panel: "#11151c",
        panel2: "#161b24",
        border: "#222a36",
        muted: "#7a8699",
        text: "#e6ecf5",
        brand: "#22d3ee",
        success: "#22c55e",
        danger: "#ef4444",
        warning: "#f59e0b",
      },
      fontFamily: {
        sans: ['"Cairo"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
