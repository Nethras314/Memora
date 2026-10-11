/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary: warm terracotta/clay (calm, grounded, culturally resonant)
        primary: {
          DEFAULT: '#b04a28',
          dark: '#8a3a1e',
          light: '#f3d8c7',
          50: '#faeae0',
          100: '#f4d6c4',
          200: '#eab9a0',
        },
        // Legacy alias so existing indigo-* classes map to the warm palette
        indigo: {
          DEFAULT: '#b04a28',
          dark: '#8a3a1e',
          light: '#f3d8c7',
          50: '#faeae0',
          100: '#f4d6c4',
          200: '#eab9a0',
        },
        // Warm neutrals
        cream: '#faf5ec',
        paper: '#fffdf9',
        ink: '#2a211b',
        muted: '#6e6055',
        faint: '#8f8378',
        line: '#e8ddcf',
        'line-soft': '#f0e8dc',
        // Supporting + semantic
        mint: '#e7efe9',
        peach: '#f7e3c8',
        saffron: '#d99a2b',
        sage: {
          DEFAULT: '#4a6b57',
          bg: '#e7efe9',
        },
        success: '#3f6b52',
        'success-bg': '#e7efe9',
        warning: '#b45309',
        'warning-bg': '#fdf0dc',
        danger: '#b3402a',
        'danger-bg': '#fae7e2',
      },
      fontFamily: {
        sans: ['Figtree', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        serif: ['Fraunces', 'Georgia', 'serif'],
      },
      borderRadius: {
        xl2: '1rem',
        xl3: '1.25rem',
      },
      boxShadow: {
        soft: '0 1px 2px rgba(42, 33, 27, 0.04), 0 4px 16px rgba(42, 33, 27, 0.06)',
        lift: '0 2px 4px rgba(42, 33, 27, 0.06), 0 12px 32px rgba(42, 33, 27, 0.12)',
      },
    },
  },
  plugins: [],
}
