import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const ranks = ['item-alpha', 'item-bravo'].map((contentId, index) => ({
  contentId, position: index + 1, score: 0.8 - index * 0.1,
  reviewStatus: 'OPEN', version: 0, caseId: null, candidateRunId: 'run-a',
  reasonCodes: [{ code: 'LOW_CTR', metric: 'ctr', value: 0.13, unit: '%' }],
}))

async function stubRanking(page: Page) {
  await page.route('**/api/v1/clients/**', route => {
    const url = new URL(route.request().url())
    if (url.pathname.endsWith('/overview')) {
      return route.fulfill({ json: { cutoff: '2025-01-01T00:00:00Z', itemCount: 2, decliningCount: 1, coverage: 1 } })
    }
    if (url.pathname.endsWith('/rankings')) {
      const query = url.searchParams.get('q')
      const shown = query ? ranks.filter(rank => rank.contentId.includes(query)) : ranks
      return route.fulfill({ json: { runId: 'run-a', nextCursor: null, pending: false, items: shown } })
    }
    const item = ranks.find(rank => url.pathname.endsWith(`/items/${rank.contentId}`))
    if (item) {
      return route.fulfill({ json: { ...item, snapshotId: 'snapshot-a', metrics: { impressions: 771, clicks: 1, ctr: 0.13 } } })
    }
    if (url.pathname.endsWith('/runs/run-a')) {
      return route.fulfill({ json: { runId: 'run-a', snapshotId: 'snapshot-a', status: 'PUBLISHED', modelId: 'model-a', eligibleRows: 2, inputRows: 2 } })
    }
    if (url.pathname.endsWith('/observations')) {
      return route.fulfill({ json: { items: [], followUp: { status: 'UNAVAILABLE', reason: 'NO_LATER_OBSERVATION' } } })
    }
    return route.fulfill({ json: { items: [], nextCursor: null } })
  })
  await page.route('**/api/v1/clients', route => route.fulfill({ json: [{ id: 'test-client', label: 'Test client' }] }))
}

test('shows loading and empty client states', async ({ page }) => {
  let reply!: () => void
  const wait = new Promise<void>(resolve => { reply = resolve })
  await page.route('**/api/v1/clients', async route => {
    await wait
    await route.fulfill({ json: [] })
  })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Loading rankings' })).toBeVisible()
  reply()
  await expect(page.getByRole('heading', { name: 'No clients available' })).toBeVisible()
})

test('reports failure and reloads the client list on retry', async ({ page }) => {
  let available = false
  await page.route('**/api/v1/clients', route => {
    if (!available) return route.fulfill({ status: 503, json: { message: 'API unavailable for verification' } })
    return route.fulfill({ json: [] })
  })
  await page.goto('/')
  await expect(page.getByRole('alert')).toContainText('API unavailable for verification')
  available = true
  await page.getByRole('button', { name: 'Retry connection' }).click()
  await expect(page.getByRole('heading', { name: 'No clients available' })).toBeVisible()
})

test('opens item evidence by keyboard and applies server search', async ({ page }) => {
  await stubRanking(page)
  await page.goto('/')
  await expect(page.getByText('Historical snapshot')).toBeVisible()
  const second = page.getByRole('button', { name: 'Inspect item-bravo' })
  await second.focus()
  await second.press('Enter')
  const heading = page.getByRole('heading', { name: 'item-bravo', exact: true })
  await expect(heading).toBeFocused()
  await expect(page.getByRole('heading', { name: 'Follow-up unavailable' })).toBeVisible()
  await page.getByRole('searchbox').fill('alpha')
  await page.getByRole('searchbox').press('Enter')
  await expect(page.getByRole('button', { name: 'Inspect item-alpha' })).toBeVisible()
  await expect(second).toHaveCount(0)
})
