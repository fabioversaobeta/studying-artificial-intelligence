import { createContext } from 'react'
import type { Language } from '@/types/api'
import { DEFAULT_LANGUAGE, translate, type MessageKey, type MessageParams } from '@/i18n'

export interface I18nContextValue {
  language: Language
  /** BCP 47 locale used by the formatters below (and exposed for custom Intl calls). */
  locale: string
  setLanguage: (language: Language) => void
  t: (key: MessageKey, params?: MessageParams) => string
  /** Date (or ISO date/datetime string) in the locale's medium date style. */
  formatDate: (value: string | Date) => string
  /** Date and time in the locale's medium/short style. */
  formatDateTime: (value: string | Date) => string
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string
}

export function createI18nValue(
  language: Language,
  locale: string,
  setLanguage: (language: Language) => void,
): I18nContextValue {
  return {
    language,
    locale,
    setLanguage,
    t: (key, params) => translate(language, key, params),
    formatDate: (value) =>
      toDate(value).toLocaleDateString(locale, { dateStyle: 'medium' }),
    formatDateTime: (value) =>
      toDate(value).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' }),
    formatNumber: (value, options) => new Intl.NumberFormat(locale, options).format(value),
  }
}

/** Date-only strings ("2026-10-08") are calendar days: parse them as local time, not UTC. */
function toDate(value: string | Date): Date {
  if (value instanceof Date) return value
  return /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value)
}

/** Without a provider (isolated component tests) the UI renders in the default language. */
export const I18nContext = createContext<I18nContextValue>(
  createI18nValue(DEFAULT_LANGUAGE, 'en-US', () => undefined),
)
