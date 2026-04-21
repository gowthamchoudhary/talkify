/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#050d05',
        primary: '#4ade80',
        card: 'rgba(255,255,255,0.04)',
      },
      fontFamily: {
        sans: ['system-ui', 'sans-serif'],
      },
      borderRadius: {
        'card': '20px',
        'button': '14px',
      },
      boxShadow: {
        'green-glow': '0 0 20px rgba(74, 222, 128, 0.3)',
      },
    },
  },
  plugins: [],
}