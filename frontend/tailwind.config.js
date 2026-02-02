/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#faf9f7",
        sage: {
          50: "#f4f6f3",
          100: "#e8ebe6",
          200: "#d1d9cc",
          300: "#a8b89e",
          400: "#8b9f82",
          500: "#6d7f64",
          600: "#56644d",
          700: "#454f3e",
        },
        gold: {
          50: "#fdfbf5",
          100: "#f9f3e6",
          200: "#f0e4c4",
        },
      },
      fontFamily: {
        serif: ["Lora", "Georgia", "serif"],
        sans: ["DM Sans", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "14px",
      },
      boxShadow: {
        soft: "0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        card: "0 2px 8px -2px rgb(0 0 0 / 0.06), 0 4px 12px -4px rgb(0 0 0 / 0.06)",
      },
    },
  },
  plugins: [],
}
