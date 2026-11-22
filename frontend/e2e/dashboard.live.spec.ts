import { expect, test } from '@playwright/test'
import type { Queue } from '../src/api'

test('opens the published queue and retains an analyst decision after reload', async ({ page }) => {
  const clientId = process.env.MVP_CLIENT_ID
  const expectedRun = process.env.MVP_RUN_ID
  const firstQueue = page.waitForResponse(response =>
    response.ok() && /\/api\/v1\/clients\/[^/]+\/rankings\?/.test(response.url()),
  )
  await page.goto(clientId ? `/?client=${encodeURIComponent(clientId)}` : '/')
  const result = await (await firstQueue).json() as Queue
  expect(result.items.length).toBeGreaterThan(1)
  if (expectedRun) expect(result.runId).toBe(expectedRun)
  await expect(page.getByRole('heading', { name: 'Content review queue' })).toBeVisible()
  const ranked = page.getByRole('button', { name: /^Inspect / })
  await expect(ranked.first()).toHaveAccessibleName(`Inspect ${result.items[0].contentId}`)
  await expect(ranked.nth(1)).toHaveAccessibleName(`Inspect ${result.items[1].contentId}`)
  await expect(page.getByRole('heading', { name: 'Ranking signals' })).toBeVisible()
  const screenshot = process.env.MVP_SCREENSHOT_PATH
  if (screenshot) {
    await expect(page.getByText('Synthetic data', { exact: true })).toBeVisible()
    await page.screenshot({ path: screenshot, animations: 'disabled', fullPage: true })
  }

  await page.getByRole('combobox', { name: 'Review status' }).selectOption('OPEN')
  await ranked.first().click()
  const inspected = page.getByRole('complementary', { name: 'Content details' })
  await inspected.getByRole('button', { name: 'Start review' }).click()
  const note = `Verified review ${new Date().toISOString()}`
  await inspected.getByRole('textbox', { name: 'Review note' }).fill(note)
  const saved = page.waitForResponse(response =>
    response.ok() && response.request().method() === 'POST' && response.url().endsWith('/actions'),
  )
  await inspected.getByRole('button', { name: 'Record action', exact: true }).click()
  const event = await (await saved).json() as { eventId: string }
  expect(event.eventId).toBeTruthy()
  await expect(inspected.getByText('Action taken', { exact: true })).toBeVisible()
  await expect(inspected.getByRole('heading', { name: 'Follow-up unavailable' })).toBeVisible()
  console.log(`Persisted review event ${event.eventId}`)

  await page.reload()
  await inspected.getByRole('button', { name: 'History' }).click()
  await expect(inspected.getByText(note, { exact: true })).toHaveCount(1)
})
