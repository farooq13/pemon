/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E8F5FF',
          100: '#B8DDFF',
          500: '#0066FF',
          600: '#0052CC',
          900: '#003D99',
        },
        secondary: {
          50: '#E6F9F0',
          500: '#00D68F',
          600: '#00B377',
        },
      },
    },
  },
  plugins: [],
}