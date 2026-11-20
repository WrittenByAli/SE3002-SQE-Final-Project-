// Reads tests/team/.env.test (base URL, room id, API tokens). Passwords follow the seed convention.
import * as fs from 'fs';
import * as path from 'path';

const file = path.resolve(__dirname, '..', '..', '.env.test');
if (!fs.existsSync(file)) {
  throw new Error(`${file} missing: run "bash tests/team/run.sh env-reset" first`);
}
const pairs = fs.readFileSync(file, 'utf8').split(/\r?\n/).filter((l) => l.includes('='))
  .map((l) => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim()]);

export const env = Object.fromEntries(pairs) as Record<string, string>;
export const ACCOUNTS = {
  user1: { username: 'user1', password: 'user1-Pass123!' },   // booker
  mgr1: { username: 'mgr1', password: 'mgr1-Pass123!' },      // moderator of room R1
} as const;
