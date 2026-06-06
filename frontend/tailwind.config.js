/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#0F1117', light: '#4A4F5C', lighter: '#8B8F9A' },
        accent: '#3B82F6',
        bg: '#F7F7F5',
        page: '#F7F7F5',
        card: '#FFFFFF',
        border: '#E5E5E5',
        danger: '#EF4444',
        success: '#22C55E',
        warning: '#F59E0B'
      }
    },
  },
  plugins: [],
}
