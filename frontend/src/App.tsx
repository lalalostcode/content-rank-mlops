import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Activity, ArrowDown, CalendarDays, ChevronDown, ChevronLeft, ChevronRight, Database, FileText, Layers3, ListFilter, ListOrdered, RefreshCw, Search, TrendingDown, X } from 'lucide-react'
import { clientPath, statusLabels, url } from './api'
import type { Client, Model, Overview, Queue, ReviewStatus, Run } from './api'
import DetailPanel, { StatusTag } from './DetailPanel'
import { count, day, label, percent, reasonLabel, time } from './format'
import { useQuery } from './use-query'

const pageSize = 8
const initialView = () => ({
  client: new URLSearchParams(location.search).get('client') ?? '',
  filter: '' as ReviewStatus | '',
  query: '',
  cursor: null as string | null,
  previous: [] as (string | null)[],
  run: null as string | null,
  item: new URLSearchParams(location.search).get('item'),
})

export default function App() {
  const [view, setView] = useState(initialView)
  const [search, setSearch] = useState('')
  const [revision, setRevision] = useState(0)
  const [clientRevision, setClientRevision] = useState(0)
  const [runOpen, setRunOpen] = useState(false)
  const dialog = useRef<HTMLDialogElement>(null)
  const focusDetails = useRef(false)

  const clients = useQuery<Client[]>('/clients', clientRevision)
  const currentClient = clients.data?.find(client => client.id === view.client) ?? clients.data?.[0]
  const client = currentClient?.id ?? view.client
  const overview = useQuery<Overview>(client ? `${clientPath(client)}/overview` : null, revision)
  const queue = useQuery<Queue>(
    client ? url(`${clientPath(client)}/rankings`, {
      limit: pageSize, runId: view.run, cursor: view.cursor, status: view.filter, q: view.query,
    }) : null,
    revision,
  )
  const runId = queue.data?.runId ?? view.run
  const run = useQuery<Run>(client && runId ? `${clientPath(client)}/runs/${encodeURIComponent(runId)}` : null, revision)
  const modelId = run.data?.modelId
  const model = useQuery<Model>(client && modelId && runOpen ? `${clientPath(client)}/models/${encodeURIComponent(modelId)}` : null, revision)
  const item = view.item ?? queue.data?.items[0]?.contentId
  const synthetic = client.startsWith('demo-client-') || client.startsWith('synthetic-') || run.data?.snapshotId.startsWith('synthetic')
  const cutoff = overview.data?.cutoff ?? run.data?.observationCutoff
  const olderSnapshot = !!cutoff && Date.now() - Date.parse(cutoff) > 90 * 86400 * 1000

  useEffect(() => {
    if (!client) return
    const target = new URL(location.href)
    target.searchParams.set('client', client)
    if (view.item) target.searchParams.set('item', view.item)
    else target.searchParams.delete('item')
    history.replaceState(null, '', target)
  }, [client, view.item])

  useEffect(() => {
    if (!item || !focusDetails.current) return
    focusDetails.current = false
    const heading = document.getElementById('detail-title')
    heading?.focus({ preventScroll: true })
    if (typeof matchMedia !== 'undefined' && matchMedia('(max-width: 1080px)').matches) {
      heading?.scrollIntoView({ block: 'nearest' })
    }
  }, [item])

  function openRun() {
    setRunOpen(true)
    dialog.current?.showModal()
  }

  function updateFilter(filter: ReviewStatus | '') {
    setView(previous => ({ ...previous, filter, cursor: null, previous: [], run: runId, item: null }))
  }

  function updateSearch(query: string) {
    setView(previous => ({ ...previous, query, cursor: null, previous: [], run: runId, item: null }))
  }

  function submitSearch(event: FormEvent) {
    event.preventDefault()
    updateSearch(search.trim())
  }

  function selectClient(next: string) {
    setSearch('')
    setView({ client: next, filter: '', query: '', cursor: null, previous: [], run: null, item: null })
  }

  function refresh() {
    setView(previous => ({ ...previous, client, run: null, cursor: null, previous: [] }))
    setRevision(previous => previous + 1)
    setClientRevision(previous => previous + 1)
  }

  function selectItem(id: string) {
    if (item === id) document.getElementById('detail-title')?.focus()
    else focusDetails.current = true
    setView(previous => ({ ...previous, run: runId, item: id }))
  }

  return <div className="app-shell">
    <a className="skip-link" href="#queue">Skip to review queue</a>
    <aside className="sidebar">
      <a className="brand" href="#top" aria-label="Content Ranking home"><span className="brand-icon"><Layers3 size={21} /></span><span>Content Ranking<small>Analyst workspace</small></span></a>
      <nav className="side-nav" aria-label="Workspace">
        <a href="#queue" aria-current="page"><ListOrdered size={18} /> Review queue</a>
        <button type="button" onClick={openRun} disabled={!runId}><Database size={17} /> Run provenance</button>
      </nav>
      <div className="environment">
        <span className={clients.error ? 'offline' : ''} aria-hidden="true" />
        <div><strong>{clients.error ? 'API unavailable' : clients.pending ? 'Connecting…' : 'Local workspace'}</strong><small>{clients.error ? 'Check server connection' : 'Content Ranking API'}</small></div>
      </div>
    </aside>

    <div className="workspace" id="top">
      <header className="topbar">
        <div className="breadcrumb"><span>Workspace</span><ChevronRight size={16} aria-hidden="true" /><strong>Review queue</strong></div>
        <div className="toolbar">
          <label className="select-control account"><span className="sr-only">Client</span><Layers3 size={16} aria-hidden="true" />
            <select value={currentClient?.id ?? ''} onChange={event => selectClient(event.target.value)} disabled={!clients.data?.length}>
              {!currentClient && <option value="">Select client</option>}
              {clients.data?.map(option => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
            <ChevronDown size={15} className="select-chevron" aria-hidden="true" />
          </label>
          <button className="button refresh-button" type="button" onClick={refresh} title="Refresh rankings"><RefreshCw size={15} /> <span>Refresh</span></button>
        </div>
      </header>

      <main className="main">
        <div className="page-heading">
          <div>
            <div className="section-label"><Activity size={16} /> Content performance</div>
            <h1>Content review queue</h1>
            <p>Investigate content performance, review ranking evidence and record a decision.</p>
          </div>
          {synthetic && <span className="data-scope"><Database size={15} /> Synthetic data</span>}
        </div>
        <section className="overview" aria-label="Client performance overview">
          <Summary name="Items analyzed" value={count(overview.data?.itemCount)} icon={FileText} />
          <Summary name="Observed declines" value={count(overview.data?.decliningCount)} icon={TrendingDown} />
          <Summary name="Ranking coverage" value={overview.data?.coverage == null ? '—' : percent(overview.data.coverage * 100)} icon={Activity} />
          <Summary name="Observation cutoff" value={day(cutoff)} icon={CalendarDays} date hint={olderSnapshot ? 'Historical snapshot' : cutoff ? 'UTC date' : 'Source date unavailable'} />
        </section>
        {overview.error && <p className="overview-error" role="alert">{overview.error}</p>}

        <div className="work-grid">
          <section className="panel queue-panel" id="queue" aria-labelledby="queue-heading">
            <div className="queue-head">
              <div><h2 id="queue-heading">Prioritized content</h2><p>Ordered by model score within the selected client.</p></div>
              {runId && <button className="button run-button" type="button" onClick={openRun}><Database size={15} /> Run details</button>}
            </div>
            <div className="queue-tools">
              <form className="search-control" role="search" onSubmit={submitSearch}>
                <Search size={16} aria-hidden="true" />
                <label className="sr-only" htmlFor="search-content">Search content IDs</label>
                <input id="search-content" type="search" placeholder="Search content IDs" value={search}
                  onChange={event => {
                    const value = event.target.value
                    setSearch(value)
                    if (!value && view.query) updateSearch('')
                  }} />
                <button type="submit" className="search-button">Search</button>
              </form>
              <label className="select-control status-filter"><span className="sr-only">Review status</span><ListFilter size={15} aria-hidden="true" />
                <select value={view.filter} onChange={event => updateFilter(event.target.value as ReviewStatus | '')}>
                  <option value="">All statuses</option>
                  {Object.entries(statusLabels).map(([key, name]) => <option key={key} value={key}>{name}</option>)}
                </select>
                <ChevronDown size={15} className="select-chevron" aria-hidden="true" />
              </label>
            </div>

            {clients.error || queue.error ? <div className="blank-state" role="alert"><Database size={30} /><h3>Rankings unavailable</h3><p>{clients.error ?? queue.error}</p><button className="button" type="button" onClick={refresh}>Retry connection</button></div>
              : clients.pending || queue.pending ? <div className="blank-state" role="status"><RefreshCw size={27} className="spinner" /><h3>Loading rankings</h3></div>
              : !clients.data?.length ? <div className="blank-state"><Database size={30} /><h3>No clients available</h3><p>Publish a scoring run to populate the review queue.</p></div>
              : !queue.data?.items.length ? <div className="blank-state"><Search size={30} /><h3>{queue.data?.pending ? 'Awaiting a scoring run' : 'No matching items'}</h3><p>{queue.data?.pending ? 'Published items will appear here.' : 'Check the search term or review status.'}</p></div>
              : <div className="table-scroll">
                <table>
                  <thead><tr><th scope="col">Rank</th><th scope="col">Content ID</th><th scope="col" aria-sort="descending">Model score <ArrowDown size={12} aria-hidden="true" /></th><th scope="col">Review status</th><th scope="col"><span className="sr-only">Inspect</span></th></tr></thead>
                  <tbody>{queue.data.items.map(rank => <tr key={rank.contentId} className={item === rank.contentId ? 'selected' : ''} onClick={() => selectItem(rank.contentId)}>
                    <td><span className={`rank-number ${rank.position <= 3 ? 'rank-top' : ''}`}>{count(rank.position)}</span></td>
                    <td><button type="button" className="item-link" aria-label={`Inspect ${rank.contentId}`} aria-pressed={item === rank.contentId} onClick={event => { event.stopPropagation(); selectItem(rank.contentId) }}>{rank.contentId}</button>
                      {rank.reasonCodes?.[0] && <small className="rank-reason">{reasonLabel(rank.reasonCodes[0].code)}</small>}</td>
                    <td className="score">{rank.score.toFixed(3)}</td>
                    <td><StatusTag status={rank.reviewStatus} /></td>
                    <td><ChevronRight size={16} className="row-chevron" aria-hidden="true" /></td>
                  </tr>)}</tbody>
                </table>
              </div>}
            {!!(queue.data?.items.length || view.previous.length) && <div className="queue-footer">
              <span>{queue.data?.items.length ? `Page ${view.previous.length + 1} · ${count(queue.data.items.length)} items` : `Page ${view.previous.length + 1}`}</span>
              <div className="pager">
                <button className="button icon-button" aria-label="Previous page" type="button" disabled={!view.previous.length || queue.pending} onClick={() => setView(previous => ({ ...previous, cursor: previous.previous.at(-1) ?? null, previous: previous.previous.slice(0, -1), item: null }))}><ChevronLeft size={18} /></button>
                <button className="button icon-button" aria-label="Next page" type="button" disabled={!queue.data?.nextCursor} onClick={() => setView(previous => ({ ...previous, run: runId, cursor: queue.data?.nextCursor ?? null, previous: [...previous.previous, previous.cursor], item: null }))}><ChevronRight size={18} /></button>
              </div>
            </div>}
          </section>

          {client && item && runId && <DetailPanel key={`${client}:${item}`} client={client} item={item} run={runId} revision={revision} onSaved={() => {
            setView(previous => ({ ...previous, run: runId, item }))
            setRevision(previous => previous + 1)
          }} />}
        </div>
      </main>
    </div>

    <dialog ref={dialog} className="run-dialog" onClose={() => setRunOpen(false)}>
      <div className="dialog-head"><div><div className="section-label"><Database size={16} /> Ranking provenance</div><h2>Scoring run</h2></div><button className="button icon-button" type="button" aria-label="Close run details" onClick={() => dialog.current?.close()}><X size={19} /></button></div>
      {(run.pending || model.pending) && <p className="muted" role="status">Loading run provenance…</p>}
      {(run.error || model.error) && <p role="alert">{run.error ?? model.error}</p>}
      {run.data && <dl className="run-meta">
        <dt>Status</dt><dd>{label(run.data.status)}</dd>
        <dt>Published</dt><dd>{time(run.data.publishedAt)}</dd>
        <dt>Observation cutoff</dt><dd>{time(run.data.observationCutoff)}</dd>
        <dt>Eligible items</dt><dd>{count(run.data.eligibleRows)} of {count(run.data.inputRows)}</dd>
        <dt>Transform</dt><dd>{run.data.transformRevision}</dd>
        <dt>Run ID</dt><dd className="identifier">{run.data.runId}</dd>
        <dt>Snapshot</dt><dd className="identifier">{run.data.snapshotId}</dd>
        <dt>Input SHA-256</dt><dd className="identifier">{run.data.inputDigest}</dd>
        <dt>Model ID</dt><dd className="identifier">{run.data.modelId}</dd>
        {model.data && <><dt>Artifact SHA-256</dt><dd className="identifier">{model.data.artifactSha256}</dd><dt>Feature schema</dt><dd>{model.data.featureSchemaVersion}</dd></>}
      </dl>}
    </dialog>
  </div>
}

type SummaryProps = { name: string; value: string; icon: typeof Activity; date?: boolean; hint?: string }

function Summary({ name, value, icon: Icon, date, hint }: SummaryProps) {
  return <div className="summary">
    <div><span className="summary-label">{name}</span><strong className={date ? 'summary-date' : ''}>{value}</strong>{hint && <small>{hint}</small>}</div>
    <span className="summary-icon"><Icon size={21} /></span>
  </div>
}
