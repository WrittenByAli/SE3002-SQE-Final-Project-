"""Validate the SQE team harness. Runs in CI (`harness` job) and locally: `bash tests/team/run.sh harness`.

Checks (each prints PASS/FAIL; exit 1 if any FAIL):
  1. required harness files exist
  2. every skill/agent has valid YAML front-matter (name matches folder/file, description present, <= 1024 chars)
  3. every relative markdown link in team docs resolves
  4. workflows: valid YAML; no escape hatches on code lines (continue-on-error: true, `|| true`, --exit-zero, set +e);
     `if: always()` only on the `ci-gate` job, which must check every result; every other job is in ci-gate.needs
  5. guard hook self-test passes and the hook command is location-independent
  6. no secret files tracked by git
  7. shell scripts use LF line endings (CRLF breaks the containers)
  8. task division covers every rubric component and every member
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
FAILS = []


def check(name, ok, detail=''):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{(' :: ' + detail) if detail and not ok else ''}")
    if not ok:
        FAILS.append(name)


REQUIRED = [
    'CLAUDE.md', 'README.md', '.claude/settings.json', '.claude/hooks/guard.py',
    '.github/workflows/ci.yml', '.github/pull_request_template.md', '.github/CODEOWNERS',
    '.github/ISSUE_TEMPLATE/defect.yml', '.github/ISSUE_TEMPLATE/task.yml', '.github/branch-protection.json', '.github/labels.yml',
    'docs/team/tasks/README.md', 'docs/team/tasks/area1-wania.md', 'docs/team/tasks/area2-fahima.md',
    'docs/team/tasks/area3-muhammad-ali.md', 'docs/team/tasks/shared-test-management.md',
    'docs/team/harness/README.md', 'docs/team/harness/github-workflow.md', 'docs/team/harness/loops.md',
    'docs/team/templates/README.md', 'docs/team/ai-use-record.md', 'docs/team/01-scope-draft.md',
    'docs/team/02-local-setup-verification.md', 'tests/team/run.sh', 'tests/team/seed/seed_rb.py', 'tests/team/seed/reset.sh',
    'infra/test-runner/Dockerfile', 'infra/indico-containers/indico-prod/docker-compose.yml',
    'infra/indico-containers/indico-prod/.env.example', 'tests/team/e2e/playwright.config.ts', 'tests/team/e2e/package-lock.json',
]
SKILLS = ['sqe-onboard', 'sqe-env', 'sqe-ai-log', 'sqe-whitebox', 'sqe-mutation', 'sqe-ci-gate', 'sqe-sonar', 'sqe-api-testing',
          'sqe-openapi-generator', 'sqe-use-cases', 'sqe-a11y', 'sqe-security', 'sqe-performance', 'sqe-test-management',
          'sqe-defect', 'sqe-viva-prep']
AGENTS = ['rubric-auditor', 'evidence-verifier', 'test-case-designer', 'mutant-analyst', 'viva-examiner']
RUBRIC = ['System & scope', 'Static analysis', 'Test plan', 'Risk register', 'White-box', 'API & integration',
          'Automated test data generation', 'Use case spec', 'Use case automation', 'Mutation & CI',
          'Usability & a11y', 'Defensive security', 'Performance & recovery', 'Defect management', 'Monitoring & completion']
MEMBERS = ['Muhammad Ali', 'Fahima', 'Wania']
ESCAPE = re.compile(r'continue-on-error\s*:\s*(true|\$\{\{)|\|\|\s*true\b|--exit-zero|\bset \+e\b')


def front_matter(path):
    text = path.read_text(encoding='utf-8')
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    return yaml.safe_load(m.group(1)) if m else None


def code_lines(text):
    return '\n'.join(ln for ln in text.splitlines() if not ln.lstrip().startswith('#'))


def main():
    # 1
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    check('1 required harness files exist', not missing, f'missing: {missing}')

    # 2
    bad = []
    for name in SKILLS:
        p = ROOT / '.claude/skills' / name / 'SKILL.md'
        try:
            fm = front_matter(p)
            if not fm or fm.get('name') != name or not fm.get('description') or len(fm['description']) > 1024:
                bad.append(name)
        except Exception as e:  # noqa: BLE001
            bad.append(f'{name} ({e.__class__.__name__})')
    for name in AGENTS:
        p = ROOT / '.claude/agents' / f'{name}.md'
        try:
            fm = front_matter(p)
            if not fm or fm.get('name') != name or not fm.get('description'):
                bad.append(name)
        except Exception as e:  # noqa: BLE001
            bad.append(f'{name} ({e.__class__.__name__})')
    check(f'2 front-matter valid ({len(SKILLS)} skills, {len(AGENTS)} agents)', not bad, f'bad: {bad}')

    # 3
    docs = [ROOT / 'CLAUDE.md', ROOT / 'README.md', *ROOT.glob('docs/team/**/*.md'), *ROOT.glob('.claude/**/*.md'),
            *ROOT.glob('.github/*.md')]
    broken = []
    for doc in docs:
        for target in re.findall(r'\]\(([^)#\s]+)(?:#[^)]*)?\)', doc.read_text(encoding='utf-8')):
            if re.match(r'[a-z]+:', target):
                continue
            if not (doc.parent / target).resolve().exists():
                broken.append(f'{doc.relative_to(ROOT)} -> {target}')
    check(f'3 markdown links resolve ({len(docs)} files)', not broken, '; '.join(broken[:10]))

    # 4
    problems = []
    for wf in sorted((ROOT / '.github/workflows').glob('*.yml')):
        text = wf.read_text(encoding='utf-8')
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            problems.append(f'{wf.name}: invalid YAML ({e})')
            continue
        if ESCAPE.search(code_lines(text)):
            problems.append(f'{wf.name}: escape hatch on a code line')
        jobs = data.get('jobs', {})
        for jid, job in jobs.items():
            cond = str(job.get('if', ''))
            if 'always()' in cond and jid != 'ci-gate':
                problems.append(f'{wf.name}: if: always() on job {jid} (only ci-gate may use it)')
            for step in job.get('steps', []):
                if 'always()' in str(step.get('if', '')):
                    problems.append(f'{wf.name}: if: always() on a step in {jid}')
        if wf.name == 'ci.yml':
            gate = jobs.get('ci-gate')
            if not gate:
                problems.append('ci.yml: no ci-gate job')
            else:
                if gate.get('name') != 'CI gate':
                    problems.append('ci.yml: ci-gate job must be named "CI gate" (branch protection requires that name)')
                needs = set(gate.get('needs', []))
                missing_needs = set(jobs) - {'ci-gate'} - needs
                if missing_needs:
                    problems.append(f'ci.yml: jobs not in ci-gate.needs (would bypass the gate): {sorted(missing_needs)}')
                gate_script = ' '.join(str(s.get('run', '')) for s in gate.get('steps', []))
                if not re.search(r'''!=\s*["']success["']''', gate_script) or 'NEEDS' not in gate_script:
                    problems.append('ci.yml: ci-gate does not check that every needs result == success')
    check('4 workflows valid, gated, no escape hatches', not problems, '; '.join(problems))

    # 5
    settings = json.loads((ROOT / '.claude/settings.json').read_text(encoding='utf-8'))
    cmds = [h['command'] for e in settings['hooks']['PreToolUse'] for h in e['hooks']]
    check('5a hook command is location-independent', all('rev-parse --show-toplevel' in c for c in cmds), str(cmds))
    r = subprocess.run([sys.executable, str(ROOT / 'tests/team/tools/guard_hook_check.py')], capture_output=True, text=True)
    check('5b guard hook self-test', r.returncode == 0, r.stdout[-400:])

    # 6
    tracked = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    secrets = [f for f in tracked if re.search(r'(^|/)(\.env|\.env\.test)$', f)]
    check('6 no secret files tracked', not secrets, str(secrets))

    # 7
    crlf = [str(p.relative_to(ROOT)) for p in [*ROOT.glob('tests/team/**/*.sh'), *ROOT.glob('infra/**/*.sh')]
            if b'\r\n' in p.read_bytes()]
    check('7 shell scripts use LF', not crlf, str(crlf))

    # 8
    tasks = (ROOT / 'docs/team/tasks/README.md').read_text(encoding='utf-8')
    missing_comp = [c for c in RUBRIC if c.lower() not in tasks.lower()]
    missing_mem = [m for m in MEMBERS if m not in tasks]
    check('8 task division covers every rubric component and member', not (missing_comp or missing_mem),
          f'components: {missing_comp} members: {missing_mem}')

    print(f'\n{len(FAILS)} check(s) failed' if FAILS else '\nharness OK')
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
