import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Language } from '@/types/api'
import { useAuth } from '@/hooks/use-auth'
import { I18nContext, createI18nValue } from '@/i18n/context'
import { DEFAULT_LANGUAGE, LOCALES, readStoredLanguage, storeLanguage } from '@/i18n'
import { useI18n } from '@/i18n/use-i18n'

/**
 * Holds the active UI language. It starts from the last language stored in the
 * browser (so login/register open in the right language), keeps `<html lang>`
 * in sync and persists every change.
 */
export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(
    () => readStoredLanguage() ?? DEFAULT_LANGUAGE,
  )

  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next)
    storeLanguage(next)
  }, [])

  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  const value = useMemo(
    () => createI18nValue(language, LOCALES[language], setLanguage),
    [language, setLanguage],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

/** Adopts the signed-in user's `preferred_language` as the UI language. Render inside AuthProvider. */
export function AuthLanguageSync() {
  const { user } = useAuth()
  const { setLanguage } = useI18n()
  const preferred = user?.preferred_language

  useEffect(() => {
    if (preferred) setLanguage(preferred)
  }, [preferred, setLanguage])

  return null
}
