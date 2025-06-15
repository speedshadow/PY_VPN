/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../templates/**/*.html', // Templates within the theme app
    '../../**/templates/**/*.html', // Templates in other apps (e.g., categories, vpn)
    '../../../templates/**/*.html', // Project-level templates in the root 'templates' folder
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
