const defaultTheme = require('tailwindcss/defaultTheme')

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Scan all HTML templates in the project's app directories.
    '../../**/templates/**/*.html',

    // Scan all custom JS files for classes.
    '../../**/static/js/**/*.js',

    // Scan Python files ONLY in our application directories, NOT the venv.
    '../../blog/**/*.py',
    '../../core/**/*.py',
    '../../theme/**/*.py',
    '../../users/**/*.py',
    '../../vpn/**/*.py',
    '../../prize_wheel/**/*.py',
  ],
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
