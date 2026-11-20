// Playwright config for the SQE project (Chromium only, as the assignment requires).
// Base URL and accounts come from tests/team/.env.test (written by `bash tests/team/run.sh env-reset`).
import { defineConfig, devices } from '@playwright/test';
import { env } from './support/env';

export default defineConfig({
  testDir: './tests',
  outputDir: '../reports/e2e/test-results',
  fullyParallel: false,          // tests share one app instance; keep runs deterministic
  workers: 1,
  retries: 0,                    // no retries: a flaky test is a defect to fix, not to hide
  timeout: 60_000,
  reporter: [['list'], ['html', { outputFolder: '../reports/e2e/html', open: 'never' }],
             ['junit', { outputFile: '../reports/e2e/junit.xml' }]],
  use: {
    baseURL: env.INDICO_BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Route browser traffic through OWASP ZAP for the passive scan: SQE_PROXY=http://localhost:8090
    proxy: process.env.SQE_PROXY ? { server: process.env.SQE_PROXY } : undefined,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
