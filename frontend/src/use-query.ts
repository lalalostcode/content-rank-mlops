import { useEffect, useState } from 'react'
import { request } from './api'

type Query<T> = { key: string | null; data: T | null; error: string | null }

export function useQuery<T>(path: string | null, revision = 0) {
  const key = path ? `${revision}:${path}` : null
  const [query, setQuery] = useState<Query<T>>({ key: null, data: null, error: null })
  useEffect(() => {
    if (!path) return
    const controller = new AbortController()
    request<T>(path, { signal: controller.signal })
      .then(data => {
        if (!controller.signal.aborted) setQuery({ key, data, error: null })
      })
      .catch((error: Error) => {
        if (!controller.signal.aborted) setQuery({ key, data: null, error: error.message })
      })
    return () => controller.abort()
  }, [key, path])

  if (query.key === key) return { data: query.data, error: query.error, pending: false }
  return { data: null, error: null, pending: key !== null }
}
