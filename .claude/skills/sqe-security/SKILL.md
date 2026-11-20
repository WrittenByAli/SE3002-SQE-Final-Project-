---
name: sqe-security
description: "Defensive security assessment on the local Indico copy: attack surface of both workflows, role access matrix with >=4 Playwright-verified access decisions, OWASP ZAP passive scan during Playwright runs, review of >=2 controls (cookies, role checks, CSRF), and pip-audit dependency audit. Defensive only, synthetic data, local instance. Use for \"security\", \"access matrix\", \"ZAP\", \"pip-audit\", \"cookie flags\"."
---

# Defensive security (Area 3, 6 marks)

Only the **local** instance, synthetic accounts, passive inspection, source review and normal application actions.
No active scanning or attacks against any external system.

## 1. Attack surface + access matrix → `docs/team/security.md`
Routes: `/rooms/api/booking/create`, `/rooms/api/bookings/{id}/{approve,reject,cancel}`, `/rooms/api/bookings/{id}`, the React
`/rooms/` UI, `/login/`. Data: reservation, room ACL, user identity/token.
| Role | Action | Expected | Observed | Evidence |
user1: create pre-booking ✔, approve ✘(403), reject ✘(403), cancel own ✔; mgr1: approve ✔, reject ✔, cancel other's ✘ (only
booker/admin, per `Reservation.can_cancel`), view any R1 booking ✔.

## 2. Playwright access checks (≥4, ≥1 allowed + ≥1 denied)
`tests/team/e2e/security/access-matrix.spec.ts`: drive the UI (or the API via `request` with each role's token), assert the
status / visible outcome, attach the response as evidence (`testInfo.attach`).

## 3. OWASP ZAP passive
```bash
docker run -d --name zap -p 8090:8090 zaproxy/zap-stable:2.16.1 zap.sh -daemon -host 0.0.0.0 -port 8090 \
  -config api.disablekey=true -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true
HTTPS_PROXY= HTTP_PROXY=http://localhost:8090 SQE_PROXY=http://localhost:8090 bash tests/team/run.sh e2e   # config honours SQE_PROXY
curl "http://localhost:8090/OTHER/core/other/htmlreport/" -o docs/team/evidence/area3/zap-passive.html
```
Passive mode only (no active scan). Review ≥2 controls, e.g. session cookie `HttpOnly`/`Secure`/`SameSite`
(note: no TLS locally, so `Secure` absent; explain), CSRF token enforcement (`indico/web/rh.py::_check_csrf`), role checks
(`can_accept`/`can_moderate`), and back up each observation with the source/config line.

## 4. Dependency audit
`pip install pip-audit==2.9.0 && pip-audit -r requirements.txt -f json -o docs/team/evidence/area3/pip-audit.json`
Record packages + versions checked (the pinned `requirements.txt`, Indico 3.3.14). Per finding: component, evidence (CVE/GHSA),
likely impact in this app, correction (upgrade version). No findings → list the verified controls.
