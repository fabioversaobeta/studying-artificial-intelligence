import { useContext } from 'react'
import { I18nContext } from '@/i18n/context'

/** Language, locale, `t()` and the Intl-based formatters for the current UI language. */
export function useI18n() {
  return useContext(I18nContext)
}

/** Shorthand for components that only need `t()`. */
export function useT() {
  return useContext(I18nContext).t
}
