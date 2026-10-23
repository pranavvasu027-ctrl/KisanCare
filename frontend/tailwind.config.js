/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          DEFAULT: '#1B4A31',
          900: '#0D2418',
          800: '#153A26',
          700: '#1B4A31',
          600: '#235D3E',
          500: '#2D754F',
          400: '#3D9969',
          100: '#E2EFE7',
          50: '#F0F7F2',
          dark: '#0E5437',
          light: '#1B8759',
        },
        agri: {
          DEFAULT: '#278653',
          dark: '#1F6C43',
          light: '#34A066',
        },
        cream: {
          50: '#FDFCF9',
          100: '#F8F6F0',
          200: '#F1ECE1',
          300: '#E5DEC8',
        },
        farm: {
          bg: '#F8F6F0',
          card: '#FFFFFF',
          text: '#1A2E22',
          muted: '#627668',
          border: '#E5E0D5',
          borderHover: '#D5CFC2',
        },
        amber: {
          DEFAULT: '#E9A23B',
          light: '#FEF6E9',
        },
        red: {
          critical: '#D9534F',
          soft: '#FDF2F2',
        },
        blue: {
          info: '#4B83C3',
          soft: '#EFF6FF',
        }
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        devanagari: ['"Noto Sans Devanagari"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
