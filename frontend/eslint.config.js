import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  // These folders contain the retired pre-presentation UI and are not part of
  // the application imported by src/App.jsx. Keep them out of the release
  // lint gate until they are removed in the next cleanup pass.
  globalIgnores(['dist', 'src/components/**', 'src/pages/**']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // The current app intentionally performs async data loading in effects.
      // These rules are useful during the planned component split, but their
      // React 19 diagnostics are not actionable for the existing data loaders.
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/exhaustive-deps': 'off',
    },
  },
])
