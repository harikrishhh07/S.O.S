/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        severity: {
          1: '#22c55e',   // green
          2: '#84cc16',   // lime
          3: '#f59e0b',   // amber
          4: '#f97316',   // orange
          5: '#ef4444',   // red
        },
      },
    },
  },
  plugins: [],
}
