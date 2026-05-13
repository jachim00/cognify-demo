/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './*.html',
    './**/*.html',
    '!./node_modules/**',
    '!./.git/**',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        ink: { 950: '#030712', 900: '#0b0f1a', 800: '#111827' },
        neon: { cyan: '#22d3ee', violet: '#a78bfa', fuchsia: '#e879f9' },
      },
      animation: {
        'mesh': 'mesh 18s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 3s linear infinite',
        'glow': 'glow 3s ease-in-out infinite alternate',
      },
      keyframes: {
        mesh: {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '33%':      { transform: 'translate(-8%, 6%) scale(1.1)' },
          '66%':      { transform: 'translate(6%, -8%) scale(0.95)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-12px)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        glow: {
          '0%':   { boxShadow: '0 0 20px rgba(34, 211, 238, 0.3), 0 0 40px rgba(167, 139, 250, 0.2)' },
          '100%': { boxShadow: '0 0 40px rgba(34, 211, 238, 0.6), 0 0 80px rgba(167, 139, 250, 0.4)' },
        },
      },
    },
  },
  plugins: [],
};
