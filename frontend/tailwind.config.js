/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f6f5f0",
        ink: "#172322",
        muted: "#71807c",
        line: "#e2e5df",
        teal: "#167c72",
        mint: "#a8e6cf",
        coral: "#c85b48",
        amber: "#b87925",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
      },
    },
  },
  plugins: [],
};
