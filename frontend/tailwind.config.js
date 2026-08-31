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
          darkest: '#081325',     // Deep Navy for sidebar/header
          dark: '#0d1d3a',        // Dark Blue
          medium: '#172d54',      // Sidebar hover/active
          light: '#233f72',       // Dark Blue borders
          cyan: '#0284c7',        // Ocean Blue accent
          teal: '#0ea5e9',        // Cyan highlight
          water: '#ebf6fc',       // Very light water blue background
          waterLight: '#f4fafd',  // Soft water card tint
          waterBorder: '#cce6f6', // Light water border
          waterBorderDark: '#93c5fd', // Accent water border
          textDark: '#0f172a',    // High-contrast primary text
          textMuted: '#475569'    // Muted text
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
