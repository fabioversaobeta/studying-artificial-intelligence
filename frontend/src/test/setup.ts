import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import { session } from '@/lib/session'

afterEach(() => {
  cleanup()
  localStorage.clear()
  session.clear()
})
