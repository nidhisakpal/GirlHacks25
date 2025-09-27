/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'goddess': {
          'athena': '#4F46E5', // Indigo for wisdom
          'aphrodite': '#EC4899', // Pink for love/wellness
          'hera': '#059669', // Emerald for career/power
        },
        'njit': {
          'red': '#CC0000',
          'gold': '#FFD700',
        }
      },
      fontFamily: {
        'serif': ['Playfair Display', 'serif'],
        'sans': ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
