# Build a secure local API and test suite

**Group A · Ethical Hacking & Web Application Security**

**Author:** Hansal Savaliya · Intern ID 2424

A local FastAPI ticket service for demonstrating authentication, authorization, input validation, and rate limiting. Its pytest suite checks both permitted and denied requests. The demo uses fictional data and targets `127.0.0.1`.

- Video: [Demonstration video](https://drive.google.com/file/d/1C0qGbq_oXyCpmH9ZxIJuaP0pHyhnPAQt/view?usp=sharing)
- Repository: [GitHub](https://github.com/hansalsavaliya200-alt/secure-local-api-test-suite-Hansal-Savaliya2424)
- Technical report: [`report/technical-report.pdf`](report/technical-report.pdf)
- Test matrix: [`docs/test-matrix.md`](docs/test-matrix.md)

## Security controls

| Control | Implementation |
|---|---|
| Authentication | Login with scrypt-hashed passwords; short-lived HS256 JWT (15 min) with pinned algorithm and required `exp`, `iat`, `sub`, `iss` claims |
| Role checks | `user`, `agent`, `admin`. The role is looked up on the server for every request, never trusted from the token |
| Object-level access | Users see only their own tickets; a foreign ticket returns 404, the same as a missing one |
| Input validation | Strict Pydantic models (unknown fields rejected), length limits, control-character checks, Content-Type (415) and body size (413) checks, UUID path parsing |
| Rate limiting | Sliding window per client address: login 5/min, everything else 60/min, `429` with `Retry-After` |
| Safe errors and logs | One error format, generic 500, no input echoed back, no tokens or passwords in logs, security headers, docs disabled by default |

**Endpoints:** `GET /health`, `POST /auth/login`, `GET /me`, `POST` and `GET /tickets`, `GET` and `DELETE /tickets/{id}`, `PATCH /tickets/{id}/status`, `GET /admin/users`, and `PATCH /admin/users/{username}/role`.

## Requirements

Python 3.10 or newer. Dependencies are in `requirements.txt` (fastapi, uvicorn, pyjwt) and `requirements-dev.txt` (adds pytest, httpx).

## Setup

Windows PowerShell (if `python` is not found, use `& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"` in its place):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`

## Run the tests

```
python -m pytest
```

Expected: `119 passed`. Saved output: `docs/evidence/pytest-output.txt`.

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

**Keep `--no-proxy-headers` for this local demo.** Uvicorn otherwise trusts forwarding headers from loopback by default and can replace the client address used by the rate limiter. This behavior was observed in the live demo and is recorded in the test matrix. In a reverse-proxy deployment, trust only the actual proxy using `--forwarded-allow-ips`.

If port `8000` is unavailable, use another port such as `8011` in the Uvicorn command and provide the same port to the demo client, for example `python scripts/demo_requests.py http://127.0.0.1:8011`.

Optional: set `APP_ENABLE_DOCS=1` to enable `/docs` for local exploration.

## Demo accounts (fictional, local only)

The fictional accounts are `alice` and `bob` (user), `carol` (agent), and `dave` (admin). Their demo passwords follow `<name>-demo-Passw0rd!`. These credentials exist only in memory and are for this local exercise; do not reuse them.

## Mutation experiment ("test the tests")

```
python scripts/mutation_check.py
```

The script weakens one control at a time in a temporary copy, checks that the suite detects each change, then retests the unmodified project. Results are saved in `docs/evidence/mutation-results.json`.

## Project layout

```
app/        API code (main, models, security, deps, ratelimit, store, errors, config)
tests/      pytest suite (auth, RBAC, validation, rate limit, errors/headers)
scripts/    demo_requests.py, mutation_check.py, build_test_matrix.py
docs/       design.md, scope-and-ethics.md, test-matrix.md, learning-journal.md, portswigger-lab-log.md, evidence/
report/     technical-report.md / .pdf
```

## Limitations

- Data and rate limits are in memory and reset on restart; state is not shared across worker processes.
- The local demonstration uses HTTP, not TLS.
- There is no token refresh or revocation flow.
- Request bodies are limited to 10 KiB, including streamed uploads.
- This project is a controlled demonstration, not a penetration test or production-ready service.

## Scope and ethics

Everything runs on 127.0.0.1 with fictional data. See [`docs/scope-and-ethics.md`](docs/scope-and-ethics.md).

## References

[`references.md`](references.md). Licence: MIT.
