// UI login helper (local Indico identity) + API helper for postcondition read-back.
import { Page, APIRequestContext, expect } from '@playwright/test';
import { ACCOUNTS, env } from './env';

export async function login(page: Page, who: keyof typeof ACCOUNTS): Promise<void> {
  const { username, password } = ACCOUNTS[who];
  await page.goto('/login/');
  await page.locator('#identifier').fill(username);
  await page.locator('#password').fill(password);
  await page.locator('#password').press('Enter');
  await expect(page).not.toHaveURL(/\/login\//);   // a failed login stays on /login/
}

export function apiHeaders(who: 'user1' | 'mgr1'): Record<string, string> {
  return { Authorization: `Bearer ${who === 'user1' ? env.USER1_TOKEN : env.MGR1_TOKEN}` };
}

export async function getBooking(request: APIRequestContext, id: number, who: 'user1' | 'mgr1' = 'mgr1') {
  const r = await request.get(`/rooms/api/bookings/${id}`, { headers: apiHeaders(who) });
  expect(r.status()).toBe(200);
  return r.json();
}
