/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          0: '#FAF9F5',
          100: '#FFFFFF',
          200: '#F0EEE6',
          300: '#DDDDDD',
        },
        text: {
          100: '#1F1E1D',
          200: '#3D3D3A',
          300: '#73726C',
          400: '#888888',
          500: '#999999',
        },
        accent: '#D97757',
        'accent-hover': '#C6613F',
      },
    },
  },
  plugins: [],
}
