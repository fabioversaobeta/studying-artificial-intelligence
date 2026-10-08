import { afterEach, describe, expect, it, vi } from 'vitest'
import { en } from '@/i18n/en'
import { ptBR } from '@/i18n/pt-br'
import {
  DEFAULT_LANGUAGE,
  SUPPORTED_LANGUAGES,
  dictionaries,
  isLanguage,
  readStoredLanguage,
  storeLanguage,
  translate,
} from '@/i18n'

const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort()

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('dictionary completeness', () => {
  const enKeys = Object.keys(en).sort()
  const ptKeys = Object.keys(ptBR).sort()

  it('has exactly the same keys in en and pt-BR', () => {
    expect(ptKeys.filter((k) => !(k in en))).toEqual([])
    expect(enKeys.filter((k) => !(k in ptBR))).toEqual([])
  })

  it.each(SUPPORTED_LANGUAGES.map((language) => [language]))(
    'has no empty values in %s',
    (language) => {
      const empty = Object.entries(dictionaries[language]).filter(([, v]) => v.trim() === '')
      expect(empty.map(([k]) => k)).toEqual([])
    },
  )

  it('keeps the same placeholders in every translation', () => {
    const mismatched = enKeys.filter(
      (key) =>
        JSON.stringify(placeholders(en[key as keyof typeof en])) !==
        JSON.stringify(placeholders(ptBR[key as keyof typeof ptBR])),
    )
    expect(mismatched).toEqual([])
  })

  it('provides both plural forms for every plural key', () => {
    const bases = enKeys.filter((k) => k.endsWith('_one')).map((k) => k.slice(0, -4))
    expect(bases.length).toBeGreaterThan(0)
    for (const base of bases) {
      expect(en).toHaveProperty(`${base}_other`)
      expect(ptBR).toHaveProperty(`${base}_other`)
    }
  })
})

describe('translate', () => {
  it('returns the string for the requested language', () => {
    expect(translate('en', 'nav.logout')).toBe('Log out')
    expect(translate('pt-BR', 'nav.logout')).toBe('Sair')
  })

  it('interpolates placeholders and leaves unknown ones untouched', () => {
    expect(translate('en', 'common.showing', { shown: 3, total: 10 })).toBe('Showing 3 of 10')
    expect(translate('pt-BR', 'common.showing', { shown: 3, total: 10 })).toBe('Mostrando 3 de 10')
    expect(translate('en', 'common.showing', { shown: 3 })).toBe('Showing 3 of {total}')
  })

  it('picks plural forms with Intl.PluralRules', () => {
    expect(translate('en', 'subjects.competencies', { count: 1 })).toBe('1 competency')
    expect(translate('en', 'subjects.competencies', { count: 5 })).toBe('5 competencies')
    expect(translate('pt-BR', 'subjects.competencies', { count: 1 })).toBe('1 competência')
    expect(translate('pt-BR', 'subjects.competencies', { count: 0 })).toBe('0 competência')
    expect(translate('pt-BR', 'subjects.competencies', { count: 5 })).toBe('5 competências')
  })

  it('falls back to English when a language lacks a key', () => {
    const original = dictionaries['pt-BR']
    const partial = { ...original } as Partial<Record<string, string>>
    delete partial['nav.logout']
    delete partial['subjects.competencies_other']
    dictionaries['pt-BR'] = partial as typeof original
    try {
      expect(translate('pt-BR', 'nav.logout')).toBe('Log out')
      expect(translate('pt-BR', 'subjects.competencies', { count: 9 })).toBe('9 competencies')
      expect(translate('pt-BR', 'nav.skip')).toBe(original['nav.skip'])
    } finally {
      dictionaries['pt-BR'] = original
    }
  })
})

describe('language storage', () => {
  it('defaults to English', () => {
    expect(DEFAULT_LANGUAGE).toBe('en')
    expect(readStoredLanguage()).toBeNull()
  })

  it('round-trips a supported language and ignores unknown values', () => {
    storeLanguage('pt-BR')
    expect(readStoredLanguage()).toBe('pt-BR')
    localStorage.setItem('lp.language', 'fr')
    expect(readStoredLanguage()).toBeNull()
    expect(isLanguage('en')).toBe(true)
    expect(isLanguage('fr')).toBe(false)
  })

  it('survives storage being unavailable', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    expect(readStoredLanguage()).toBeNull()
    expect(() => storeLanguage('pt-BR')).not.toThrow()
  })
})
