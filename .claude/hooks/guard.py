#!/usr/bin/env python3
"""PreToolUse guard for the SQE project (Claude Code hook).

Blocks (exit code 2, reason on stderr, which Claude sees):
  1. `git commit` / `git push` while secrets are staged/committed: .env, tests/team/.env.test, Indico API tokens (indp_...).
  2. Edits that add CI escape hatches to workflows (continue-on-error, `|| true`, --exit-zero).
  3. Edits that LOWER a threshold in tests/team/quality-gates.yml.
  4. `git push --force` to main.
Everything else passes (exit 0). The hook is deliberately simple, so read it, it is short.
"""
import json
import re
import subprocess
import sys

TOKEN_RE = re.compile(r'indp_[A-Za-z0-9_-]{20,}')
SECRET_PATHS = re.compile(r'(^|/)(\.env|\.env\.test)$')
ESCAPE_RE = re.compile(r'continue-on-error\s*:\s*true|\|\|\s*true|--exit-zero|set \+e')
GATE_FILE = 'tests/team/quality-gates.yml'


def block(msg):
    print(f'BLOCKED by .claude/hooks/guard.py: {msg}', file=sys.stderr)
    sys.exit(2)


def git(*args):
    try:
        return subprocess.run(['git', *args], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return ''


def check_bash(cmd):
    if re.search(r'\bgit\s+push\b.*(--force\b|-f\b)', cmd) and re.search(r'\bmain\b', cmd):
        block('force-push to main is not allowed.')
    if re.search(r'\bgit\s+commit\b', cmd):
        staged = git('diff', '--cached', '--name-only').split()
        bad = [p for p in staged if SECRET_PATHS.search(p)]
        if bad:
            block(f'secret files staged: {bad}. Unstage them (git restore --staged ...).')
        if TOKEN_RE.search(git('diff', '--cached', '-U0')):
            block('an Indico API token (indp_...) is in the staged diff. Remove it; tokens live in tests/team/.env.test.')


def code_only(text):
    """Drop YAML/shell comment lines so documentation that *mentions* a forbidden pattern is not flagged."""
    return '\n'.join(ln for ln in text.splitlines() if not ln.lstrip().startswith('#'))


def numbers(text):
    return {m.group(1): float(m.group(2)) for m in re.finditer(r'^\s*(\w+)\s*:\s*([0-9.]+)', text, re.M)}


def check_edit(tool, inp):
    path = (inp.get('file_path') or '').replace('\\', '/')
    new = inp.get('new_string') or inp.get('content') or ''
    old = inp.get('old_string') or ''
    if '.github/workflows/' in path and ESCAPE_RE.search(code_only(new)) and not ESCAPE_RE.search(code_only(old)):
        block('CI escape hatch (continue-on-error / || true / --exit-zero / set +e) is forbidden by the assignment.')
    if path.endswith(GATE_FILE):
        if tool == 'Write':
            try:
                with open(path, encoding='utf-8') as f:
                    old = f.read()
            except OSError:
                return
        before, after = numbers(old), numbers(new)
        lowered = [k for k in after if k in before and after[k] < before[k] and not k.endswith('_max')]
        raised_max = [k for k in after if k in before and k.endswith('_max') and after[k] > before[k]]
        if lowered or raised_max:
            block(f'quality gate weakened ({lowered + raised_max}). Gates only ratchet up; a human must do this with justification.')


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool = data.get('tool_name', '')
    inp = data.get('tool_input', {}) or {}
    if tool in ('Bash', 'PowerShell'):
        check_bash(inp.get('command', ''))
    elif tool in ('Edit', 'Write', 'MultiEdit'):
        check_edit(tool, inp)
    return 0


if __name__ == '__main__':
    sys.exit(main())
