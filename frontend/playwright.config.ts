import { defineConfig, devices } from '@playwright/test'

const baseURL = process.env.MVP_BASE_URL ?? 'http://127.0.0.1:5173'

export default defineConfig({
  testDir: './e2e',
  workers: 1,
  outputDir: './node_modules/.cache/dashboard-test-results',
  use: {
    ...devices['Desktop Chrome'],
    channel: process.env.PLAYWRIGHT_CHANNEL ?? 'chrome',
    baseURL,
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
  },
  webServer: process.env.MVP_BASE_URL ? undefined : {
    command: 'npm run dev',
    url: baseURL,
    reuseExistingServer: true,
  },
  projects: [
    { name: 'component', testMatch: '**/*.component.spec.ts' },
    { name: 'live', testMatch: '**/*.live.spec.ts' },
  ],
})
