export const statusLabels = {
  OPEN: 'Open',
  IN_REVIEW: 'In review',
  ACTION_TAKEN: 'Action taken',
  DEFERRED: 'Deferred',
  NO_ACTION: 'No action',
  RESOLVED: 'Resolved',
} as const

export type ReviewStatus = keyof typeof statusLabels
export type Decision = 'act' | 'defer' | 'no_action'
export type Client = { id: string; label: string }
export type Overview = {
  snapshotId: string | null
  cutoff: string | null
  itemCount: number
  decliningCount: number | null
  coverage: number | null
}
export type Reason = { code: string; metric: string; value: number | null; unit: string }
export type Rank = {
  contentId: string
  position: number
  score: number
  reviewStatus: ReviewStatus
  version: number
  caseId: string | null
  candidateRunId: string | null
  reasonCodes: Reason[]
}
export type Queue = {
  runId: string | null
  items: Rank[]
  nextCursor: string | null
  pending: boolean
}
export type Detail = Rank & {
  cutoff: string | null
  snapshotId: string
  metrics: Record<string, number | null>
  observationWindowStart: string | null
  observationWindowEnd: string | null
}
export type Event = {
  eventId: string
  caseId: string
  resultingVersion: number
  actor: string
  occurredAt: string
  eventType: string
  runId: string
  snapshotId: string
  priorStatus: ReviewStatus | null
  newStatus: ReviewStatus
  decision: Decision | null
  note: string | null
}
export type Paged<T> = { items: T[]; nextCursor: string | null }
export type Observation = {
  snapshotId: string
  cutoff: string | null
  sourceRelease: string
  windowStart: string | null
  windowEnd: string | null
  metrics: Record<string, number | null>
}
export type Observations = {
  items: Observation[]
  followUp: {
    status: 'AVAILABLE' | 'UNAVAILABLE'
    reason?: string
    baseline?: Observation
    later?: Observation
    deltas?: Record<string, number>
  } | null
}
export type Run = {
  runId: string
  status: string
  snapshotId: string
  inputDigest: string
  observationCutoff: string | null
  transformRevision: string
  modelId: string
  inputRows: number
  eligibleRows: number
  publishedAt: string | null
}
export type Model = {
  modelId: string
  artifactSha256: string
  featureSchemaVersion: string
  registryUri: string | null
}

export class ApiError extends Error {
  constructor(readonly status: number, message: string) {
    super(message)
  }
}

export function url(path: string, params?: Record<string, string | number | null>) {
  const query = new URLSearchParams()
  for (const [name, value] of Object.entries(params ?? {})) {
    if (value !== null && value !== '') query.set(name, String(value))
  }
  return query.size ? `${path}?${query}` : path
}

export const clientPath = (client: string) => `/clients/${encodeURIComponent(client)}`
export const itemPath = (client: string, item: string) => `${clientPath(client)}/items/${encodeURIComponent(item)}`

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/v1${path}`, { cache: 'no-store', ...options })
  } catch (error) {
    if (options?.signal?.aborted) throw error
    throw new ApiError(0, 'The local API could not be reached.')
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(
      response.status,
      payload?.message ?? (response.status >= 500 ? 'The local API is unavailable.' : 'The request could not be completed.'),
    )
  }
  if (payload === null) throw new ApiError(response.status, 'The local API returned an invalid response.')
  return payload as T
}
