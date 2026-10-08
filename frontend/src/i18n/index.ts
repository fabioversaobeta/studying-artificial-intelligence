import type { Language } from '@/types/api'
import { en } from '@/i18n/en'
import { ptBR } from '@/i18n/pt-br'

/** Every key of the English dictionary, including plural variants (`key_one`, ...). */
type RawKey = keyof typeof en

/** Keys callers may pass to `t()`: plural variants are requested by their base key. */
export type MessageKey = RawKey extends infer K
  ? K extends `${infer Base}_${'one' | 'other'}`
    ? Base
    : K
  : never

export type MessageParams = Record<string, string | number>
export type Dictionary = Record<RawKey, string>

export const DEFAULT_LANGUAGE: Language = 'en'
export const SUPPORTED_LANGUAGES: readonly Language[] = ['en', 'pt-BR']

/** BCP 47 locale handed to `Intl` for each UI language. */
export const LOCALES: Record<Language, string> = { en: 'en-US', 'pt-BR': 'pt-BR' }

export const dictionaries: Record<Language, Dictionary> = { en, 'pt-BR': ptBR }

export function isLanguage(value: unknown): value is Language {
  return typeof value === 'string' && (SUPPORTED_LANGUAGES as readonly string[]).includes(value)
}

function interpolate(template: string, params?: MessageParams): string {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  )
}

/**
 * Looks `key` up in `language`, falling back to English when the language has
 * no entry. If `params.count` is a number, the plural variant (`key_one`,
 * `key_other`, chosen with Intl.PluralRules) is preferred over the plain key.
 */
export function translate(language: Language, key: MessageKey, params?: MessageParams): string {
  const table = dictionaries[language] as Partial<Record<string, string>>
  const fallback = dictionaries[DEFAULT_LANGUAGE] as Record<string, string>
  const lookup = (k: string) => table[k] ?? fallback[k]

  let template: string | undefined
  if (params && typeof params.count === 'number') {
    const category = new Intl.PluralRules(LOCALES[language]).select(params.count)
    template = lookup(`${key}_${category}`) ?? lookup(`${key}_other`)
  }
  template ??= lookup(key)
  return interpolate(template ?? key, params)
}

const STORAGE_KEY = 'lp.language'

/** Last language used, kept for logged-out screens. Not sensitive; storage may be unavailable. */
export function readStoredLanguage(): Language | null {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    return isLanguage(value) ? value : null
  } catch {
    return null
  }
}

export function storeLanguage(language: Language): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, language)
  } catch {
    // Storage blocked: the preference still works for this page view.
  }
}
