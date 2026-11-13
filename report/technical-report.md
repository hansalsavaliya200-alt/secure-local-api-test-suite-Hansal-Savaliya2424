# Secure Local API and Test Suite

## Task 2 · Group A · Ethical Hacking & Web Application Security

|  |  |
|---|---|
| **Author** | Hansal Savaliya · Intern ID 2424 |
| **Report date** | 13 November 2026 |
| **Repository** | `<ADD GITHUB URL>` |
| **Demonstration video** | `<ADD VIDEO URL>` |
| **Project scope** | Defensive test application bound to `127.0.0.1` |

## Executive summary

This project implements a small helpdesk-ticket API with authentication, role-based and object-level authorization, request validation, and rate limiting. The purpose was not just to demonstrate successful requests: the test suite also checks denied requests, boundary values, and whether tests fail when a control is deliberately weakened in a temporary project copy.

Verification on 13 November 2026 produced **117 passing pytest cases** across **76 test functions**, a successful live demo, and detection of all **five** injected test mutations. A live test also exposed an interaction between Uvicorn's proxy-header handling and the application's address-based login limit. Launching with `--no-proxy-headers` corrected the observed behavior; the before-and-after output is retained in the evidence directory.

These are results from a controlled local demonstration, not a penetration test, production readiness assessment, or proof that the API is free of vulnerabilities.

| Project measure | Recorded result |
|---|---|
| Automated suite | 117 passed; 76 test functions |
| Live demo | All checks passed against `127.0.0.1:8001` |
| Mutation experiment | 5 of 5 injected weaknesses detected |
| Retest after mutations | 117 passed on the unmodified code |
| Generated test matrix | 76 of 76 test functions pass |

## 1. Objective and scope

The objective was to build a repeatable, safe demonstration of common API security controls and verify both permitted and denied behavior. The implementation uses fictional accounts and tickets, and runs on the local machine. The API has three roles:

| Role | Intended permissions |
|---|---|
| `user` | Create tickets and access their own tickets |
| `agent` | Read tickets and update ticket status |
| `admin` | Administrative user and ticket operations |

The project tests four connected areas: authentication and token handling, function- and object-level access control, input validation, and request-rate/resource controls. PortSwigger Academy labs are performed only in PortSwigger's lab environment; details of the two screenshot-confirmed labs are recorded separately in `docs/portswigger-lab-log.md`.

All API and live-demo requests target `127.0.0.1`. Demo accounts (`alice`, `bob`, `carol`, `dave`), tickets, and test values are fictional. No real user credentials, personal data, or third-party targets were used for the API tests. The complete scope statement and data provenance are in `docs/scope-and-ethics.md`.

## 2. System design

The application is a FastAPI service with an in-memory user/ticket store. Its request path is deliberately ordered so inexpensive controls run before route work:

**Request → address-based rate limit → size/content-type checks → bearer-token verification → current role check → schema validation → ticket ownership check → response, security headers, and safe log entry**

Authentication establishes identity; authorization is evaluated separately. A JWT contains the subject but not trusted authority. The current role is loaded from the store on every request, so an already-issued token does not preserve a role after a demotion.

| Control | Implementation and expected behavior |
|---|---|
| Password verification | Passwords use salted scrypt hashes; comparison uses `hmac.compare_digest`. Unknown usernames also incur a dummy hash check [12][13]. |
| Access tokens | HS256 is explicitly pinned; `exp`, `iat`, `sub`, and `iss` are required and the issuer is verified. Tokens expire after 15 minutes [8][9]. |
| Authentication errors | Missing, malformed, expired, or invalid tokens receive a consistent `401` response with `WWW-Authenticate: Bearer` [10]. |
| Role authorization | Route dependencies check the current server-side role. A logged-in user without the required role receives `403` [14]. |
| Ticket ownership | Users can access their own tickets. A foreign ticket and a missing ticket both return `404` to avoid confirming that a ticket exists [6][14]. |
| Request validation | Pydantic models reject extra fields, constrain lengths and enumerated values, and reject disallowed control characters [15][16]. |
| Request handling | Non-JSON request bodies receive `415`; requests over the configured 10 KiB `Content-Length` limit receive `413` [17]. |
| Rate limiting | Sliding windows allow 5 login requests per 60 seconds and 60 requests per 60 seconds on other routes; excess requests receive `429` and `Retry-After` [11][17]. |
| Response/log hardening | Standardized errors, generic `500` responses, request IDs, security headers, and logs that omit query strings and credentials [17][18]. Interactive API docs are disabled by default. |

Implementation details are in `app/security.py`, `app/deps.py`, `app/models.py`, `app/ratelimit.py`, `app/main.py`, and `docs/design.md`. These controls follow the cited guidance on JWT best practices, authorization, validation, password storage, REST security, and logging [9][13][14][15][17][18].

## 3. Verification method

Verification uses three complementary layers because an in-process test client does not exercise every behavior of a real ASGI server.

1. **Automated pytest suite.** The app is exercised with a fresh store and rate limiter for each test. A fake clock makes sliding-window boundaries repeatable without waiting. Cases cover positive flows, denied requests, malformed tokens, validation boundaries, error responses, role changes, and rate-limit behavior.
2. **Live HTTP demo.** `scripts/demo_requests.py` sends requests to a running Uvicorn server and prints expected and actual status codes. This checks the API through the actual server launch path, including the forwarded-address behavior.
3. **Mutation experiment.** `scripts/mutation_check.py` copies the project to a temporary directory, weakens one control per copy, and runs pytest. A mutation is detected when the weakened copy fails tests. The script then retests the original, unmodified project. The real source files are not mutated.

The curated expected/actual matrix is generated from pytest's JUnit XML by `scripts/build_test_matrix.py`. Evidence files are saved in `docs/evidence/`; the report summarizes selected cases rather than replacing that detailed matrix.

### Reproduction

From the project directory in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
python scripts/mutation_check.py
```

In a first terminal, create an ephemeral local signing key and start the API. Port `8000` is the documented default; `8001` was used for the captured demo because `8000` was already occupied on that machine.

```powershell
$env:APP_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(40))"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --no-proxy-headers
```

In a second terminal:

```powershell
python scripts/demo_requests.py http://127.0.0.1:8001
```

Use the documented `--no-proxy-headers` option for the local demo. If running behind a trusted reverse proxy in another environment, configure only the actual proxy as trusted; do not treat a client-supplied forwarding header as identity. The demo applies a per-address login limit, so wait 60 seconds before repeating it.

## 4. Test results

### Automated cases

The captured pytest run used Python 3.12.10 and pytest 9.2.0. It collected 117 cases and completed with **117 passed in 4.15 seconds**. The principal evidence is `docs/evidence/pytest-output.txt`.

| Scenario | Expected | Actual |
|---|---:|---:|
| Valid login and access to `/me` | `200` | `200` |
| Missing or tampered bearer token | `401` | `401` |
| Unsigned (`alg: none`), expired, or wrong-issuer JWT | `401` | `401` |
| User reads own ticket / another user's ticket | `200` / `404` | `200` / `404` |
| User or agent lists administrative accounts | `403` | `403` |
| Admin lists accounts | `200` | `200` |
| Health endpoint body | `{"status":"ok"}` only | `{"status":"ok"}` |
| Client attempts to set ticket `owner` | `422` | `422` |
| Form body instead of JSON | `415` | `415` |
| Ticket title at 100 / 101 characters | `201` / `422` | `201` / `422` |
| Request over configured size limit | `413` | `413` |
| Sixth login attempt within the window | `429` with `Retry-After` | `429` |
| Malformed ticket UUID | `404`, not `500` | `404` |

This is a representative selection, not the complete inventory. The full curated list, including additional normal, negative, and edge cases, appears in `docs/test-matrix.md`.

### Cross-check against the shared starter-pack fixtures

The shared `01_WEB_SECURITY` resource folder contains mock CSV fixtures describing example endpoints and hypothetical weaknesses. These are reference material, not observations about this API; none of those fixture weaknesses is claimed as a project finding [21].

| Fixture theme | Related project check | Scope distinction |
|---|---|---|
| Overlong input | Ticket title boundaries (100 accepted, 101 rejected) and oversized-body rejection | The fixture's `/profile` endpoint is not part of this project. |
| Script-like input/output handling | `test_script_like_text_is_stored_as_data_and_returned_as_json` checks JSON content type, exact returned text, and `nosniff` | This is an API JSON check, not a browser-rendered HTML/XSS test. |
| Role-restricted access | `test_admin_users_list_by_role` and ticket ownership tests | The fixture's `/admin` endpoint is not part of this project. |
| Limited health output | `test_health_response_contains_only_status` asserts the exact `{"status":"ok"}` response | The fixture is a prompt for coverage; its hypothetical health disclosure is not a finding here. |

### Mutation experiment: can the tests detect weakened controls?

Every listed weakness was inserted only into a temporary copy. All five mutations were detected; the unmodified code then passed all 117 cases. The run is preserved in `docs/evidence/mutation-check-output.txt` and `docs/evidence/mutation-results.json`.

| Deliberately weakened control in temporary copy | Failing tests | Detected |
|---|---:|---|
| Allow any logged-in user to list accounts | 2 | Yes |
| Allow any logged-in user to delete tickets | 2 | Yes |
| Remove ticket ownership enforcement | 2 | Yes |
| Ignore unknown request fields | 4 | Yes |
| Raise the login limit so it is effectively disabled | 5 | Yes |

The 15 failures above are test detections across the five separate mutation runs; they are not 15 unique vulnerabilities in the final application. The original implementation was retested successfully afterward.

## 5. Findings and remediation

Findings below describe observed project-test results. “Pass” means the stated behavior was verified by the recorded tests; it is not a claim that the system has no other weaknesses.

| ID | Finding | Evidence and result |
|---|---|---|
| F-01 | Function- and object-level authorization are enforced for tested cases. | User/agent administrative requests were denied; an owner could read their ticket; a different user received the same `404` behavior as a missing ticket. Related mutations were detected. |
| F-02 | Token verification rejects tested invalid credentials and token forms. | Missing, modified, unsigned, expired, wrong-issuer, and wrong-key tokens were rejected with `401`. Role changes are read from the server rather than trusted from the old token. |
| F-03 | Strict request schemas reject tested mass-assignment and malformed-input cases. | An `owner` field and invalid payloads were rejected; content type, field length, request size, and UUID cases returned the expected error codes. |
| F-04 | Login limiting works in app tests and in the corrected live launch. | Five attempts were allowed, the next was limited with `429` and `Retry-After`; the fake-clock test verified window expiry. |
| F-05 | Initial live launch exposed a forwarded-header / rate-limit interaction; the launch configuration was corrected and retested. | With Uvicorn's default proxy-header behavior, the forged `X-Forwarded-For` check returned `401` rather than the expected `429`. Starting with `--no-proxy-headers` made the same check return `429`; the live demo then passed. Before/after output is in `docs/evidence/xff-before-after.txt`. |
| F-06 | The health endpoint exposes only its status field in the tested response. | `GET /health` returned exactly `{"status":"ok"}`; a focused regression test now guards the response shape. |

**F-05 analysis.** The application's limiter keys on the address it receives from the ASGI request. In the first live run, the default server configuration trusted the forwarded address, allowing a client-supplied `X-Forwarded-For` value to appear as a different client. The in-process `TestClient` tests did not expose the server configuration interaction. Disabling proxy-header handling for this local run restored the expected per-client limit. This illustrates why deployment configuration must be included in end-to-end verification; the corrective launch option is documented in the README. The observed behavior and configuration are consistent with Uvicorn's proxy-header settings [20]; the specific reference URL could not be opened during the reference check, as noted in `references.md`.

## 6. Limitations and residual risks

- **In-memory storage and limiter:** users, tickets, and counters reset on restart and are not shared across worker processes. This design is for a small local demo, not a multi-worker service.
- **Local HTTP only:** TLS and remote deployment are outside the demonstrated scope.
- **Request-size enforcement:** the current limit checks `Content-Length`; a chunked body without that header is not capped by this check.
- **Address-based rate limiting:** clients sharing an address share a quota, and distributed sources may not be constrained by one address-based counter.
- **Token lifecycle:** access tokens expire after 15 minutes, but there is no refresh-token flow or token revocation. A stolen token remains usable until expiry or the associated account is disabled.
- **Signing-key operations:** the demo accepts a sufficiently long environment key or creates a random startup key. Key rotation and persistent secret management are not implemented.
- **Test scope:** passing tests verify selected requirements and regressions. Mutation checks show that these tests detect the inserted weaknesses, not that every possible attack or flaw has been found.

## 7. Recommended next steps

For a larger or production-oriented system, use persistent storage and a shared rate-limit backend; enforce limits while reading request bytes, not only from `Content-Length`; implement token revocation and key rotation; and add a real-server integration test so the proxy-header behavior remains covered automatically. A dependency vulnerability scan and further authorized testing in a local lab would add evidence, but neither was performed for this report.

## 8. Use of AI tools

Claude and GitHub Copilot helped draft code and documents. I ran and reviewed the project.

## 9. Sources and supporting evidence

Bracketed source numbers refer to `references.md`, which records titles, URLs, access-date notes, and how each source was used. The specific WSTG authorization URL redirected to a general landing page and the Uvicorn URL did not resolve during the reference check; see the notes in that file.

Primary project evidence:

- Automated run: `docs/evidence/pytest-output.txt`
- Live requests: `docs/evidence/demo-output.txt`
- Mutation results: `docs/evidence/mutation-check-output.txt` and `docs/evidence/mutation-results.json`
- Before/after launch behavior: `docs/evidence/xff-before-after.txt`
- Expected/actual matrix: `docs/test-matrix.md`
- Scope and synthetic data: `docs/scope-and-ethics.md`
