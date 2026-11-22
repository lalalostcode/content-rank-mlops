import { useRef, useState } from 'react'
import { Activity, CalendarDays, ClipboardList, FileSearch, History, MousePointer2, ScanSearch, Target } from 'lucide-react'
import { ApiError, clientPath, itemPath, request, statusLabels, url } from './api'
import type { Decision, Detail, Event, Observations, Paged, ReviewStatus } from './api'
import { count, day, decimal, label, percent, reasonLabel, time } from './format'
import { useQuery } from './use-query'

export function StatusTag({ status }: { status: ReviewStatus }) {
  return <span className={`status-tag status-${status.toLowerCase()}`}><i aria-hidden="true" />{statusLabels[status]}</span>
}

const decisionLabels: Record<Decision, string> = { act: 'Record action', defer: 'Defer', no_action: 'Close without action' }
const followUpReasons: Record<string, string> = {
  NO_RECORDED_ACTION: 'Record an action to establish a baseline for comparison.',
  NO_LATER_OBSERVATION: 'No later observation is available for this content item.',
  INCOMPARABLE_OBSERVATIONS: 'The available observation windows cannot be compared.',
}

type Props = { client: string; item: string; run: string; revision: number; onSaved: () => void }

type Mutation = {
  method: 'PATCH' | 'POST'
  path: string
  body: Record<string, string | number>
}

export default function DetailPanel({ client, item, run, revision, onSaved }: Props) {
  const endpoint = itemPath(client, item)
  const [tab, setTab] = useState<'evidence' | 'history'>('evidence')
  const [historyCursor, setHistoryCursor] = useState<string | null>(null)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null)
  const attempt = useRef<{ fingerprint: string; key: string } | null>(null)

  const detail = useQuery<Detail>(`${clientPath(client)}/rankings/${encodeURIComponent(run)}/items/${encodeURIComponent(item)}`, revision)
  const history = useQuery<Paged<Event>>(url(`${endpoint}/actions`, { cursor: historyCursor }), revision)
  const observations = useQuery<Observations>(
    detail.data ? url(`${endpoint}/observations`, { caseId: detail.data.caseId }) : null,
    revision,
  )

  async function save({ method, path, body }: Mutation) {
    const data = JSON.stringify(body)
    const fingerprint = `${method}:${path}:${data}`
    if (attempt.current?.fingerprint !== fingerprint) {
      attempt.current = { fingerprint, key: crypto.randomUUID() }
    }
    setSaving(true)
    setMessage(null)
    try {
      await request(path, {
        method,
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': attempt.current.key },
        body: data,
      })
      attempt.current = null
      setMessage({ ok: true, text: 'Review saved.' })
      setNote('')
      setHistoryCursor(null)
      onSaved()
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        attempt.current = null
        setMessage({ ok: false, text: 'This review changed. Check the latest status before trying again.' })
        onSaved()
      } else {
        setMessage({ ok: false, text: error instanceof Error ? error.message : 'Could not save the review.' })
      }
    } finally {
      setSaving(false)
    }
  }

  function changeStatus(rank: Detail, status: ReviewStatus) {
    const body: Mutation['body'] = { status, expectedVersion: rank.version }
    if (rank.caseId) {
      body.caseId = rank.caseId
      body.runId = run
    } else if (rank.candidateRunId) {
      body.candidateRunId = rank.candidateRunId
    } else return
    void save({ method: 'PATCH', path: `${endpoint}/status`, body })
  }

  function recordDecision(rank: Detail, decision: Decision) {
    if (!rank.caseId) return
    void save({
      method: 'POST',
      path: `${endpoint}/actions`,
      body: { caseId: rank.caseId, runId: run, expectedVersion: rank.version, decision, note: note.trim() },
    })
  }

  const rank = detail.data
  const metrics = rank?.metrics ?? {}
  const followUp = observations.data?.followUp
  const baseline = followUp?.baseline
  const later = followUp?.later

  return <aside className="panel detail-panel" id="item-detail" aria-label="Content details">
    <div className="detail-head">
      <div className="section-label"><FileSearch size={16} /> Content details</div>
      <h2 tabIndex={-1} id="detail-title">{item}</h2>
      {rank && <div className="detail-meta"><span>Rank {count(rank.position)}</span><StatusTag status={rank.reviewStatus} /></div>}
    </div>
    <div className="detail-tabs" aria-label="Content detail view">
      <button type="button" aria-pressed={tab === 'evidence'} onClick={() => setTab('evidence')}><ScanSearch size={15} /> Evidence</button>
      <button type="button" aria-pressed={tab === 'history'} onClick={() => setTab('history')}><History size={15} /> History</button>
    </div>
    {detail.pending && <div className="detail-body muted" role="status">Loading item details…</div>}
    {detail.error && <div className="detail-body" role="alert">{detail.error}</div>}
    {rank && tab === 'evidence' && <div className="detail-body">
      <div className="detail-metrics">
        <div><span><Activity size={14} /> Impressions</span><strong>{count(metrics.impressions)}</strong></div>
        <div><span><MousePointer2 size={14} /> Clicks</span><strong>{count(metrics.clicks)}</strong></div>
        <div><span><Target size={14} /> Click-through</span><strong>{percent(metrics.ctr)}</strong></div>
        <div><span><ScanSearch size={14} /> Avg position</span><strong>{decimal(metrics.avgPosition)}</strong></div>
      </div>
      <section className="inspector-section" aria-labelledby="signal-heading">
        <h3 id="signal-heading">Ranking signals</h3>
        {rank.reasonCodes?.length ? <ul className="signals">{rank.reasonCodes.map((reason, index) =>
          <li key={`${reason.code}-${index}`}>
            <span>{reasonLabel(reason.code)}</span>
            {reason.value != null && <strong>{decimal(reason.value)}{reason.unit === '%' ? '%' : reason.unit ? ` ${reason.unit}` : ''}</strong>}
          </li>
        )}</ul> : <p className="muted">No ranking signals were published for this item.</p>}
        <p className="window"><CalendarDays size={14} /> {rank.observationWindowStart && rank.observationWindowEnd
          ? `${day(rank.observationWindowStart)} – ${day(rank.observationWindowEnd)}`
          : 'Observation window unknown'}</p>
      </section>
      <section className="inspector-section" aria-labelledby="followup-heading">
        <h3 id="followup-heading">{followUp?.status === 'AVAILABLE' ? 'Follow-up observations' : 'Follow-up unavailable'}</h3>
        {baseline && later && followUp?.status === 'AVAILABLE'
          ? <>
            <dl className="comparison">
              <dt>Metric</dt><dd>{day(baseline.cutoff)}</dd><dd>{day(later.cutoff)}</dd><dd>Change</dd>
              <dt>Impressions</dt><dd>{count(baseline.metrics.impressions)}</dd><dd>{count(later.metrics.impressions)}</dd><dd>{count(followUp.deltas?.impressions)}</dd>
              <dt>Clicks</dt><dd>{count(baseline.metrics.clicks)}</dd><dd>{count(later.metrics.clicks)}</dd><dd>{count(followUp.deltas?.clicks)}</dd>
              <dt>Click-through</dt><dd>{percent(baseline.metrics.ctr)}</dd><dd>{percent(later.metrics.ctr)}</dd><dd>{followUp.deltas?.ctr == null ? '—' : `${decimal(followUp.deltas.ctr)} pp`}</dd>
            </dl>
            <p className="window"><CalendarDays size={14} /> {day(later.windowStart)} – {day(later.windowEnd)} · {later.sourceRelease}</p>
          </>
          : <p className="muted">{observations.pending
            ? 'Checking later observations…'
            : observations.error ?? followUpReasons[followUp?.reason ?? 'NO_RECORDED_ACTION'] ?? 'A comparable later observation is required.'}</p>}
      </section>
    </div>}
    {rank && tab === 'history' && <div className="detail-body">
      <h3>Review history</h3>
      {history.pending && <p className="muted" role="status">Loading events…</p>}
      {history.error && <p role="alert">{history.error}</p>}
      {history.data && (history.data.items.length ? <ol className="event-list">
        {history.data.items.map(event => <li key={event.eventId}>
          <span className="event-mark"><ClipboardList size={15} /></span>
          <div><strong>{statusLabels[event.newStatus] ?? label(event.eventType)}</strong>
            <p className="event-meta">{event.actor} · {time(event.occurredAt)}</p>
            {event.note && <p className="event-note">{event.note}</p>}
          </div>
        </li>)}
      </ol> : <p className="muted">No review events yet.</p>)}
      {(historyCursor || history.data?.nextCursor) && <div className="history-pager">
        {historyCursor && <button type="button" className="button" onClick={() => setHistoryCursor(null)}>First events</button>}
        {history.data?.nextCursor && <button type="button" className="button" onClick={() => setHistoryCursor(history.data!.nextCursor)}>Later events</button>}
      </div>}
    </div>}
    {rank && <div className="review-footer">
      {rank.reviewStatus === 'OPEN' && rank.candidateRunId &&
        <button type="button" className="button primary full-width" disabled={saving} onClick={() => changeStatus(rank, 'IN_REVIEW')}>Start review</button>}
      {rank.reviewStatus === 'DEFERRED' && rank.caseId &&
        <button type="button" className="button primary full-width" disabled={saving} onClick={() => changeStatus(rank, 'IN_REVIEW')}>Resume review</button>}
      {rank.reviewStatus === 'ACTION_TAKEN' && rank.caseId &&
        <button type="button" className="button primary full-width" disabled={saving} onClick={() => changeStatus(rank, 'RESOLVED')}>Resolve review</button>}
      {rank.reviewStatus === 'IN_REVIEW' && rank.caseId && <>
        <label className="note-label" htmlFor="review-note">Review note</label>
        <textarea id="review-note" value={note} onChange={event => setNote(event.target.value)} maxLength={1000} rows={3} placeholder="Optional" />
        <div className="decision-actions">{(Object.entries(decisionLabels) as [Decision, string][]).map(([decision, name]) =>
          <button key={decision} type="button" className={`button ${decision === 'act' ? 'primary' : ''}`} disabled={saving} onClick={() => recordDecision(rank, decision)}>{name}</button>
        )}</div>
      </>}
      {message && <p className={`save-message ${message.ok ? 'positive' : 'negative'}`} role={message.ok ? 'status' : 'alert'}>{message.text}</p>}
    </div>}
  </aside>
}
