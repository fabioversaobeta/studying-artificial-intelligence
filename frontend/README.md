# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.

## Tests

Vitest + Testing Library + jsdom (config in `vite.config.ts`, setup in `src/test/setup.ts`).

```bash
npm test           # single run
npm run test:watch # watch mode
```

Test files live next to the code as `*.test.ts` / `*.test.tsx`.

## Localisation (i18n)

UI strings live in `src/i18n/en.ts` (source of truth, fallback) and
`src/i18n/pt-br.ts`. Use them with `const t = useT()` (or `useI18n()` for
`formatDate`, `formatDateTime`, `formatNumber`); never hardcode visible text,
`aria-label`s or placeholders. Design: docs/DECISIONS.md, "UI localisation".

- **New string**: add the key to `en.ts` and to `pt-br.ts` (TypeScript and
  `src/i18n/i18n.test.ts` fail if one is missing or the `{placeholders}`
  differ), then `t('area.key', { name })`.
- **Plurals**: add `key_one` and `key_other` and call `t('key', { count })`.
- **New language**: add it to `Language` in `src/types/api.ts` (and the backend
  enum), create `src/i18n/<code>.ts` typed as `Dictionary`, register it in
  `dictionaries`, `SUPPORTED_LANGUAGES` and `LOCALES` in `src/i18n/index.ts`,
  and add it to `LANGUAGE_OPTIONS` in `src/pages/settings-page.tsx`.
- **Tests** render in English with no provider; wrap in `I18nProvider` (and set
  `localStorage['lp.language']`) to test another language.
