/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          darkest: '#070b19', // Deep navy background
          dark: '#0e172c',    // Card/Sidebar backgrounds
          medium: '#1b2a47',  // Interactive slates
          light: '#3a506b',   // Border slates
          cyan: '#00b4d8',    // Scientific data cyan
          teal: '#48cae4',    // Highlight light cyan
          accent: '#5bc0be',  // Ocean teal accent
          neutral: '#f8f9fa'  // Standard scientific white background
        }
      },
      fontFamily: {
        mono: ['Fira Code', 'JetBrains Mono', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}
