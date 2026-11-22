const integer = new Intl.NumberFormat('en')
const fractional = new Intl.NumberFormat('en', { maximumFractionDigits: 2 })
const calendar = new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeZone: 'UTC' })
const timestamp = new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' })

export const count = (value: number | null | undefined) => value == null ? '—' : integer.format(value)
export const decimal = (value: number | null | undefined) => value == null ? '—' : fractional.format(value)
export const day = (value: string | null | undefined) => value && Number.isFinite(Date.parse(value)) ? calendar.format(new Date(value)) : 'Unknown'
export const time = (value: string | null | undefined) => value && Number.isFinite(Date.parse(value)) ? `${timestamp.format(new Date(value))} UTC` : 'Unknown'
export const label = (token: string) => token.toLowerCase().replaceAll('_', ' ').replace(/^./, letter => letter.toUpperCase())
export const percent = (value: number | null | undefined) => value == null ? '—' : `${decimal(value)}%`

const reasonLabels: Record<string, string> = {
  LOW_CTR: 'Low click-through rate',
  STALE_CONTENT: 'Older content',
  OBSERVED_DECLINE: 'Observed decline',
  SEARCH_VISIBILITY: 'Search visibility',
}

export const reasonLabel = (code: string) => reasonLabels[code] ?? label(code)
