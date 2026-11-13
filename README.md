# Secure Local API and Test Suite

Task 2, Group A (Ethical Hacking & Web Application Security).
**Author:** Hansal Savaliya, Intern ID 2424.

A small **local** helpdesk-ticket API (FastAPI) with authentication, role checks, input validation and rate limiting, plus a pytest suite that tests both allowed and denied requests.

- Video: `<ADD VIDEO LINK AFTER UPLOAD>`
- Technical report: [`report/technical-report.pdf`](report/technical-report.pdf)
- Test matrix: [`docs/test-matrix.md`](docs/test-matrix.md)

## What it does

| Control | Implementation |
|---|---|
| Authentication | Login with scrypt-hashed passwords; short-lived HS256 JWT (15 min) with pinned algorithm and required `exp`, `iat`, `sub`, `iss` claims |
| Role checks | `user`, `agent`, `admin`. The role is looked up on the server for every request, never trusted from the token |
| Object-level access | Users see only their own tickets; a foreign ticket returns 404, the same as a missing one |
| Input validation | Strict Pydantic models (unknown fields rejected), length limits, control-character checks, Content-Type (415) and body size (413) checks, UUID path parsing |
| Rate limiting | Sliding window per client address: login 5/min, everything else 60/min, `429` with `Retry-After` |
| Safe errors and logs | One error format, generic 500, no input echoed back, no tokens or passwords in logs, security headers, docs disabled by default |

Endpoints: `GET /health`, `POST /auth/login`, `GET /me`, `POST/GET /tickets`, `GET/DELETE /tickets/{id}`, `PATCH /tickets/{id}/status`, `GET /admin/users`, `PATCH /admin/users/{username}/role`.

## Requirements

Python 3.10 or newer. Dependencies are in `requirements.txt` (fastapi, uvicorn, pyjwt) and `requirements-dev.txt` (adds pytest, httpx).

## Setup

Windows PowerShell (if `python` is not found, use `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"` in its place):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`

## Run the tests

```
python -m pytest
```

Expected: `116 passed`. Saved output: `docs/evidence/pytest-output.txt`.

## Run the API and the demo client

Terminal 1 (PowerShell):

```powershell
$env:APP_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(40))"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

(bash: `export APP_SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(40))")`.)

Terminal 2:

```
python scripts/demo_requests.py
```

It prints each allowed and denied request with expected and actual status. Wait 60 seconds between runs because login is rate limited. Output from a real run: `docs/evidence/demo-output.txt`.

**Important:** keep `--no-proxy-headers`. By default uvicorn trusts `X-Forwarded-For` from 127.0.0.1 and rewrites the client address, which lets a client dodge the rate limit. The demo found this (see the test matrix, section B2). Behind a real reverse proxy you would instead list only that proxy with `--forwarded-allow-ips`.

Optional: set `APP_ENABLE_DOCS=1` to enable `/docs` for local exploration.

## Demo accounts (fictional, local only)

`alice` and `bob` (user), `carol` (agent), `dave` (admin). Passwords follow `<name>-demo-Passw0rd!`. They exist only in memory and protect nothing.

## Mutation experiment ("test the tests")

```
python scripts/mutation_check.py
```

Works on a temporary copy: it removes one control at a time (for example the admin role check), confirms the suite fails, then retests the real code. Results: `docs/evidence/mutation-results.json`.

## Project layout

```
app/        API code (main, models, security, deps, ratelimit, store, errors, config)
tests/      pytest suite (auth, RBAC, validation, rate limit, errors/headers)
scripts/    demo_requests.py, mutation_check.py, build_test_matrix.py
docs/       design.md, scope-and-ethics.md, test-matrix.md, learning-journal.md, portswigger-lab-log.md, evidence/
report/     technical-report.md / .pdf
```

## Limitations

In-memory data and rate limits (reset on restart, single process); plain HTTP on localhost; no refresh tokens or revocation; body size limit uses `Content-Length` only, so chunked uploads are not capped; not a penetration test. Details in the report.

## Scope and ethics

Everything runs on 127.0.0.1 with fictional data. See [`docs/scope-and-ethics.md`](docs/scope-and-ethics.md).

## AI use

Claude and GitHub Copilot helped draft code and documents. I ran and reviewed the project.

## References

[`references.md`](references.md). Licence: MIT.
