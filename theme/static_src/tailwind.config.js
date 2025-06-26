const defaultTheme = require('tailwindcss/defaultTheme')

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Templates HTML
    '../../**/templates/**/*.html',
    '../../**/templates/**/*.django',
    // JavaScript
    '../../**/static/js/**/*.js',
    '../../**/static/js/**/*.jsx',
    // Python
    '../../**/*.py',
    '!../../venv/**/*.py',
    '!../../**/migrations/*.py',
  ],
  mode: 'jit',
  safelist: [
    'prose',
    'prose-xl',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
        serif: ['Lora', ...defaultTheme.fontFamily.serif],
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
