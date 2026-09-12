/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        indigo: {
          DEFAULT: '#4943a5',
          dark: '#37327f',
          light: '#625cc0'
        },
        cream: '#faf8f2',
        paper: '#fffefb',
        mint: '#dceee9',
        peach: '#f9e7c5',
        line: '#e5dfd4'
      }
    },
  },
  plugins: [],
}
