/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#09111d'
        }
      },
      fontFamily: {
        mono: ['monospace', 'Courier New'],
      }
    },
  },
  plugins: [],
}
