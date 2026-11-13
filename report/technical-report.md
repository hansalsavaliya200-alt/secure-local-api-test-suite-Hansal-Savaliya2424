# Secure Local API and Test Suite

**Name:** Hansal Savaliya  **Intern ID:** 2424
**Task:** Task 2, Group A: Ethical Hacking & Web Application Security
**Date:** November 2026
**Repository:** `<ADD GITHUB URL>`  **Video:** `<ADD VIDEO URL>`

## 1. Problem

The task was to build a local API that implements authentication, role checks, input validation and rate limiting, and to test both allowed and denied requests. Web APIs fail most often through missing checks, not clever attacks: a missing ownership check exposes other users' data, a missing role check lets an ordinary user do admin work, and a missing limit allows unlimited password guessing (OWASP API Security Top 10, 2023 [6]). The goal was therefore a small working API *and* evidence that each control really works, including evidence that the tests would notice if a control were removed.

## 2. Scope and safety

Everything runs on 127.0.0.1 on my own computer. All data is synthetic: four demo users (`alice`, `bob`, `carol`, `dave`) and example tickets. No real credentials, personal data or third-party systems were used or tested. PortSwigger labs are completed only in PortSwigger's own environment, and OWASP Juice Shop is optional and local only. The scope statement is in `docs/scope-and-ethics.md`.

## 3. Design

The API is a small helpdesk-ticket service built with FastAPI. Three roles exist: `user` (own tickets only), `agent` (read all tickets, change status) and `admin` (everything, including deleting tickets and changing roles).

Each request passes through the same steps:

1. **Pre-checks:** rate limit, then size (`Content-Length`) and `Content-Type`.
2. **Authentication:** verify a bearer JWT and load the user from the store.
3. **Role check:** compare the user's current role with the roles the route allows.
4. **Validation:** strict models that reject unknown fields.
5. **Object-level check:** may this caller touch *this* ticket?
6. **Safe response:** a single error format, security headers and a request ID.

Key design decisions (full table in `docs/design.md`):

- **The token proves identity, not authority.** It carries only the username. The role is read from the store on every request, so a demotion takes effect immediately.
- **A foreign ticket returns 404, not 403,** so the response does not confirm that the ticket exists.
- **The rate limiter keys on the real socket address,** never on `X-Forwarded-For`, because the client controls that header [17].

## 4. Implementation

| Control | How it is done | File |
|---|---|---|
| Passwords | scrypt (N=2^14, r=8, p=1) with a random salt; constant-time comparison; a dummy hash is checked for unknown users so timing and message match [12][13] | `app/security.py` |
| Tokens | HS256 JWT, 15-minute lifetime, algorithm pinned, claims `exp`, `iat`, `sub`, `iss` required, issuer checked [8][9] | `app/security.py` |
| 401 handling | One response for every authentication failure, with `WWW-Authenticate: Bearer` [10] | `app/deps.py` |
| Role checks | `require_roles(...)` dependency on each protected route; deny by default [14] | `app/deps.py`, `app/main.py` |
| Validation | Pydantic models with `extra="forbid"`, length limits, enumerated values, control-character rejection, UUID path parsing [15][16] | `app/models.py` |
| Request limits | `Content-Type` must be JSON (415); body larger than 10 KB is refused (413) | `app/main.py` |
| Rate limiting | Sliding window per client address: login 5 per 60 s, other routes 60 per 60 s; `429` with `Retry-After` [11] | `app/ratelimit.py` |
| Errors and logs | Generic 500; validation errors never echo the submitted value; log lines contain method, path and status but no query string, token or password [17][18] | `app/errors.py`, `app/main.py` |
| Hardening | `X-Content-Type-Options`, `Cache-Control: no-store`, `Referrer-Policy`, CSP and `X-Frame-Options`; `/docs` disabled by default | `app/main.py` |
| Startup safety | The signing key must be at least 32 characters; if none is set a random one is generated and a warning is logged | `app/config.py` |

## 5. Test method

Testing used three layers, each answering a different question.

1. **Automated suite (pytest, 116 cases in 75 test functions).** Tests call the app through FastAPI's `TestClient` with a fresh store and rate limiter for every test, and a fake clock so that the 60-second windows can be tested instantly. The tests cover normal use, denied requests, boundary values and abuse cases, following the planning approach in the WSTG [3][4].
2. **Live demo client** (`scripts/demo_requests.py`). It starts from the outside, as a real client would, against a real `uvicorn` server, and prints expected against actual status for 24 requests.
3. **Mutation experiment** (`scripts/mutation_check.py`). A passing test suite does not show that the tests are *capable of failing*. The script copies the project to a temporary directory, removes one control at a time, runs the suite and expects failures, then retests the unmodified code.

The expected-against-actual matrix is in `docs/test-matrix.md`. It is generated from the real pytest run, not typed by hand.

## 6. Results

**Automated suite:** 116 cases passed (`docs/evidence/pytest-output.txt`).

**Selected allowed and denied requests (from the live demo):**

| Request | Expected | Actual |
|---|---|---|
| `GET /me` without a token | 401 | 401 |
| `GET /me` with a tampered token | 401 | 401 |
| alice creates a valid ticket | 201 | 201 |
| alice sends an unknown field `owner` | 422 | 422 |
| form data instead of JSON | 415 | 415 |
| bob reads alice's ticket | 404 | 404 |
| carol (agent) reads alice's ticket | 200 | 200 |
| alice (user) lists all accounts | 403 | 403 |
| dave (admin) lists all accounts | 200 | 200 |
| alice makes herself admin | 403 | 403 |
| carol (agent) deletes a ticket | 403 | 403 |
| dave (admin) deletes a ticket | 204 | 204 |
| 6th login attempt in a minute | 429 | 429 |

**Mutation experiment:** all five inserted weaknesses were detected (2, 2, 2, 4 and 5 tests failed respectively). The five were: any user can list accounts, any user can delete tickets, any user can read any ticket, unknown fields accepted, and unlimited login attempts. The retest on the unmodified code passed all 116 cases.

**One failure found and fixed.** The first live run of the demo client showed one failed check: a request with a forged `X-Forwarded-For` header after the login limit was reached returned 401 instead of 429, so the limit had been bypassed. The unit tests had not caught it because `TestClient` does not go through uvicorn. The server log showed the request arriving from the forged address `203.0.113.9`. The cause is that uvicorn trusts forwarding headers from 127.0.0.1 by default and rewrites the client address [20]. Starting uvicorn with `--no-proxy-headers` fixed it, and the same check then returned 429 (`docs/evidence/xff-before-after.txt`). The README now requires the flag. The lesson is that a control can be correct in the application code and still be undone by the way the server is started, so tests must also run against the real server.

## 7. Limitations

- **State is in memory.** Users, tickets and rate-limit counters reset on restart and are not shared between processes, so the limiter would not work correctly with several workers.
- **No HTTPS.** The demo runs over HTTP on localhost. TLS is not implemented or tested.
- **Body size is capped by the `Content-Length` header only,** so a chunked upload without that header is not capped. A production service should cap the bytes actually read, or rely on a reverse proxy.
- **No refresh tokens, token revocation or multi-factor authentication.** A stolen token works until it expires after 15 minutes.
- **Rate limiting by address only.** Users behind one shared address share a limit, and an attacker with many addresses is not slowed.
- **Symmetric signing key held by the server.** It is generated at start-up or read from an environment variable and is not rotated.
- **The tests are not a penetration test.** They show that the checks I thought of work; they do not prove that no vulnerability exists.

## 8. Future work

Add a persistent database and a shared rate-limit store; enforce the byte cap on streamed bodies; add refresh tokens with revocation; add account lockout or progressive delays; add an automated test that starts a real server so the proxy-header issue is covered by the suite; run a dependency vulnerability scan; and test the API with a proxy tool such as OWASP ZAP in my own lab.

## 9. Use of AI tools

Claude and GitHub Copilot helped draft code and documents. I ran and reviewed the project.

## 10. Sources

Full list with URLs, access dates and what each was used for: `references.md`. Numbers in brackets above refer to that table.
