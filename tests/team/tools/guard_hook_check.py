"""Self-test for .claude/hooks/guard.py (run by check_harness.py). Exits non-zero on any mismatch."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / '.claude/hooks/guard.py'
FP = 'push --' + 'force'  # split so this file's own text never looks like a command

CASES = [  # (description, payload, expected exit code)
    ('allow normal bash', {'tool_name': 'Bash', 'tool_input': {'command': 'git status'}}, 0),
    ('block force push to main', {'tool_name': 'Bash', 'tool_input': {'command': f'git {FP} origin main'}}, 2),
    ('allow push feature branch', {'tool_name': 'Bash', 'tool_input': {'command': 'git push -u origin feat/x'}}, 0),
    ('block || true in workflow', {'tool_name': 'Edit', 'tool_input': {
        'file_path': 'D:\\r\\.github\\workflows\\ci.yml', 'old_string': 'run: pytest', 'new_string': 'run: pytest ||' + ' true'}}, 2),
    ('block continue-on-error', {'tool_name': 'Edit', 'tool_input': {
        'file_path': '.github/workflows/ci.yml', 'old_string': 'x', 'new_string': 'continue-on-' + 'error: true'}}, 2),
    ('allow a COMMENT that mentions || true', {'tool_name': 'Write', 'tool_input': {
        'file_path': '.github/workflows/new.yml', 'content': '# rule: never use ||' + ' true\njobs: {}\n'}}, 0),
    ('block || true on a code line under a comment', {'tool_name': 'Write', 'tool_input': {
        'file_path': '.github/workflows/new.yml', 'content': '# ok\n    run: make ||' + ' true\n'}}, 2),
    ('allow normal workflow edit', {'tool_name': 'Edit', 'tool_input': {
        'file_path': '.github/workflows/ci.yml', 'old_string': 'a', 'new_string': 'run: pytest -q'}}, 0),
    ('block lowering coverage gate', {'tool_name': 'Edit', 'tool_input': {
        'file_path': 'tests/team/quality-gates.yml', 'old_string': '  statement_min: 25', 'new_string': '  statement_min: 20'}}, 2),
    ('allow raising coverage gate', {'tool_name': 'Edit', 'tool_input': {
        'file_path': 'tests/team/quality-gates.yml', 'old_string': '  statement_min: 25', 'new_string': '  statement_min: 40'}}, 0),
    ('block raising a _max', {'tool_name': 'Edit', 'tool_input': {
        'file_path': 'tests/team/quality-gates.yml', 'old_string': '  bugs_max: 0', 'new_string': '  bugs_max: 3'}}, 2),
]


def run(payload, cwd=ROOT, raw=None):
    data = raw if raw is not None else json.dumps(payload)
    return subprocess.run([sys.executable, str(HOOK)], input=data, text=True, capture_output=True, cwd=cwd).returncode


def main():
    failures = []
    for desc, payload, want in CASES:
        got = run(payload)
        print(f'{"ok " if got == want else "FAIL"} {desc}: exit {got} (want {want})')
        if got != want:
            failures.append(desc)
    got = run(None, raw='not json')
    print(f'{"ok " if got == 0 else "FAIL"} allow garbage stdin: exit {got} (want 0)')
    if got != 0:
        failures.append('garbage stdin')

    commit = {'tool_name': 'Bash', 'tool_input': {'command': 'git commit -m x'}}
    with tempfile.TemporaryDirectory() as d:
        env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
        g = lambda *a: subprocess.run(['git', *a], cwd=d, capture_output=True, env=env)  # noqa: E731
        g('init', '-q')
        Path(d, '.env').write_text('X=1\n')
        g('add', '.env')
        got = run(commit, cwd=d)
        print(f'{"ok " if got == 2 else "FAIL"} block commit with .env staged: exit {got} (want 2)')
        failures += [] if got == 2 else ['.env staged']
        g('restore', '--staged', '.env')
        Path(d, 'notes.txt').write_text('token=indp_' + 'A' * 30 + '\n')
        g('add', 'notes.txt')
        got = run(commit, cwd=d)
        print(f'{"ok " if got == 2 else "FAIL"} block commit with API token in diff: exit {got} (want 2)')
        failures += [] if got == 2 else ['token staged']
        g('reset', '-q')
        Path(d, 'notes.txt').write_text('clean\n')
        g('add', 'notes.txt')
        got = run(commit, cwd=d)
        print(f'{"ok " if got == 0 else "FAIL"} allow clean commit: exit {got} (want 0)')
        failures += [] if got == 0 else ['clean commit']

    print(f'\nguard hook: {len(failures)} failure(s)')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
