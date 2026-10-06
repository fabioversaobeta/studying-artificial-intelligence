import type { Paged } from '@/services/api-client'

/** Builds a `Paged<T>` fixture; `total` defaults to the number of items. */
export function paged<T>(items: T[], total = items.length): Paged<T> {
  return { items, total }
}
