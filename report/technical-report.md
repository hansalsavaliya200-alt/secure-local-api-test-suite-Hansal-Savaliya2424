---
toc: true
toc-depth: 2
---

# Secure Local API and Test Suite

## Task 2 · Group A · Ethical Hacking & Web Application Security

|  |  |
|---|---|
| **Author** | Hansal Savaliya · Intern ID 2424 |
| **Report date** | 13 November 2026 |
| **Repository** | https://github.com/hansalsavaliya200-alt/secure-local-api-test-suite-Hansal-Savaliya2424 |
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

| Scope boundary | Included | Excluded |
|---|---|---|
| Application | This repository's FastAPI service on loopback | Public deployment, external services, and other people's systems |
| Data | Synthetic, in-memory users, tickets, tokens, and test payloads | Real accounts, live customer data, and production secrets |
| Verification | Automated tests, the local HTTP demo, and temporary-copy mutations | A penetration test, external scanning, or a claim of production readiness |
| Training resources | PortSwigger Academy labs in PortSwigger's own lab environment | Testing any unrelated site or network |

The success criteria were observable behavior rather than a claim that the system is vulnerability-free: expected requests should succeed, unauthorized and malformed requests should be rejected consistently, the local demo should pass through the real ASGI server, and deliberately weakened controls should cause tests to fail.

## 2. Threat model and security objectives

This is a small local training API, so the threat model is intentionally bounded. It considers an unauthenticated caller able to send requests to the local service, an authenticated user attempting actions outside their role or ticket ownership, and malformed or repeated requests. It does not model a remote production deployment, a compromised operating system, or a distributed multi-worker service.

| Asset or boundary | Relevant threat | Security objective |
|---|---|---|
| User identity and bearer tokens | Forged, altered, expired, or unsigned token; password guessing | Verify signed tokens with fixed rules; limit login attempts; avoid logging credentials |
| Ticket records and ownership | A user reads another user's ticket or supplies an `owner` field | Derive ownership from verified identity and enforce object-level checks |
| Administrative actions | A lower-privileged user lists accounts, changes roles, or deletes tickets | Require the current server-side role for each operation |
| Request parser and application resources | Invalid fields, oversized bodies, invalid media types, or excessive requests | Bound input, reject unsupported shapes, and return predictable errors |
| Response and logs | Internal exception detail or submitted values disclose sensitive data | Keep errors generic, avoid reflecting input, and exclude credentials and query strings from logs |
| Client address and rate-limit key | An untrusted forwarding header changes the apparent client | Key limits from the address supplied by the ASGI request and configure proxy trust explicitly |

The trust boundaries are the HTTP request entering the ASGI application, the bearer token being verified, the server-side in-memory store, and the Uvicorn deployment configuration. These boundaries explain why both in-process tests and a live local-server check are included. The detailed allowed-use rules and synthetic-data provenance are in `docs/scope-and-ethics.md`.

## 3. System design

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
| Rate limiting | Sliding windows use the ASGI client address and allow 5 login requests per 60 seconds and 60 requests per 60 seconds on other routes; excess requests receive `429` and `Retry-After` [11][17]. |
| Response/log hardening | Standardized errors, generic `500` responses, request IDs, security headers, and logs that omit query strings and credentials [17][18]. Interactive API docs are disabled by default. |

Implementation details are in `app/security.py`, `app/deps.py`, `app/models.py`, `app/ratelimit.py`, `app/main.py`, and `docs/design.md`. These controls follow the cited guidance on JWT best practices, authorization, validation, password storage, REST security, and logging [9][13][14][15][17][18].

### Route and authorization map

Authentication and authorization are separate decisions: a valid token establishes the caller's identity, while each route applies its own role or ownership rule. The current role is reloaded from the local store for each authenticated request.

| Route | Access rule | Expected behavior |
|---|---|---|
| `GET /health` | Public | Returns only `{"status":"ok"}` |
| `POST /auth/login` | Public, rate-limited | Valid fictional credentials receive a short-lived bearer token |
| `GET /me` | Any authenticated role | Returns the caller's username and current role |
| `POST /tickets` | Any authenticated role | Creates a ticket owned by the authenticated caller |
| `GET /tickets` and `GET /tickets/{id}` | Authenticated; users see their own tickets, agents/admins may view all | A foreign individual ticket is indistinguishable from a missing ticket (`404`) |
| `PATCH /tickets/{id}/status` | Agent or admin | Updates a non-closed ticket; unknown or closed tickets are not silently changed |
| `DELETE /tickets/{id}` | Admin | Deletes a ticket; other roles are denied |
| `GET /admin/users` and `PATCH /admin/users/{username}/role` | Admin | Provides administrative user operations; self-demotion is rejected with `409` |

### Request and response lifecycle

The middleware applies cheap request guards before route logic. Authentication then resolves identity, authorization checks current permissions, schema validation constrains input, and object-level checks enforce ticket ownership.

```text
HTTP request
  -> rate / body-size / media-type pre-checks
  -> bearer-token verification and user lookup (where required)
  -> current-role authorization
  -> strict request schema validation
  -> ticket ownership or state check
  -> response with request ID, security headers, and safe log entry
```

The implementation returns a uniform JSON error envelope. Validation responses identify failing fields but do not echo submitted values; unexpected server exceptions produce a generic `500` response while details remain in server logs. The logging check asserts that tokens, passwords, and query strings are not recorded.

## 4. Verification method

Verification uses three complementary layers because an in-process test client does not exercise every behavior of a real ASGI server.

1. **Automated pytest suite.** The app is exercised with a fresh store and rate limiter for each test. A fake clock makes sliding-window boundaries repeatable without waiting. Cases cover positive flows, denied requests, malformed tokens, validation boundaries, error responses, role changes, and rate-limit behavior.
2. **Live HTTP demo.** `scripts/demo_requests.py` sends requests to a running Uvicorn server and prints expected and actual status codes. This checks the API through the actual server launch path, including the forwarded-address behavior.
3. **Mutation experiment.** `scripts/mutation_check.py` copies the project to a temporary directory, weakens one control per copy, and runs pytest. A mutation is detected when the weakened copy fails tests. The script then retests the original, unmodified project. The real source files are not mutated.

The curated expected/actual matrix is generated from pytest's JUnit XML by `scripts/build_test_matrix.py`. Evidence files are saved in `docs/evidence/`; the report summarizes selected cases rather than replacing that detailed matrix.

### Test environment and repeatability

| Item | Recorded value |
|---|---|
| Operating system | Windows |
| Python | 3.12.10 |
| Test runner | pytest 9.2.0 |
| Application target | `127.0.0.1`; captured live demo used port `8001` because `8000` was occupied |
| Test state | Fresh application/store fixtures; synthetic identities and tickets |
| Time-dependent rate-limit tests | Injectable clock, so boundary and reset checks do not sleep |
| Mutation isolation | Each weakened control is applied in a temporary project copy; the working source is retested unmodified |

The live demo is a separate layer rather than a duplicate of `TestClient`: it validates the actual Uvicorn launch configuration and HTTP behavior. This distinction mattered for the forwarded-address failure documented below.

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

## 5. Test results

### Automated cases

The captured pytest run used Python 3.12.10 and pytest 9.2.0. It collected 117 cases and completed with **117 passed in 4.15 seconds**. The principal evidence is `docs/evidence/pytest-output.txt`.

The case counts below are taken from the captured JUnit XML; parametrized tests contribute more than one case.

| Test module | Cases | Coverage focus |
|---|---:|---|
| `test_auth.py` | 29 | Login, token claims, malformed credentials, current identity |
| `test_errors_headers.py` | 11 | Health response shape, safe errors, security headers, request IDs, logging |
| `test_ratelimit.py` | 8 | Thresholds, retry metadata, expiry/reset, forwarded-header behavior |
| `test_rbac.py` | 32 | Role checks, ownership, role updates, administrative actions |
| `test_validation.py` | 37 | Schema constraints, content types, body size, boundary and malformed input |
| **Total** | **117** | **76 test functions, including parametrized cases** |

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

### Live HTTP demonstration

The captured demo produced **24 passing checks** through Uvicorn. It covered public and unauthenticated responses, ticket creation and validation, object-level access, role-restricted operations, the login threshold, and the forged-forwarding-header case. The printed output in `docs/evidence/demo-output.txt` records each expected and actual status; no bearer-token values are printed.

The initial server run did not pass every check: with Uvicorn's default proxy-header handling, the forwarded-address check returned `401` instead of `429`. The before/after record in `docs/evidence/xff-before-after.txt` shows the check passing after the local launch was changed to `--no-proxy-headers`. This is kept as a configuration finding rather than being hidden by reporting only the successful rerun.

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

### Requirements-to-evidence traceability

| Security objective | Verification evidence | Recorded result |
|---|---|---|
| Authenticate valid users and reject invalid or altered tokens | Login, malformed-token, claim, and expiry tests | Expected `200`/`401` behavior passed |
| Enforce role and object-level permissions | RBAC tests and live role checks | Unauthorized actions returned `403`; foreign tickets returned `404` |
| Reject malformed and excessive input | Schema, boundary, content-type, UUID, and size tests | Expected `422`, `415`, `413`, or `404` responses passed |
| Limit repeated login attempts | Sliding-window tests, live sixth-attempt check, mutation test | `429` and `Retry-After` observed; removal of the limit was detected |
| Avoid leaking sensitive details | Error-shape, input non-echo, header, and logging tests | Generic errors and expected security/logging properties passed |
| Ensure tests detect selected regressions | Five temporary-copy mutations and real-code retest | All five detected; real code passed 117 cases |

## 6. Findings and remediation

The table distinguishes controls verified by tests from the configuration behavior observed during live verification. “Verified” means the stated behavior passed its recorded checks; it is not a claim that the system has no other weaknesses. No severity score is assigned because this was a bounded local exercise, not a vulnerability assessment.

| ID | Finding | Evidence and result |
|---|---|---|
| F-01 · Control verified | Function- and object-level authorization for tested cases | User/agent administrative requests were denied; an owner could read their ticket; a different user received the same `404` behavior as a missing ticket. Related mutations were detected. |
| F-02 · Control verified | Token verification for tested invalid credentials and token forms | Missing, modified, unsigned, expired, wrong-issuer, and wrong-key tokens were rejected with `401`. Role changes are read from the server rather than trusted from the old token. |
| F-03 · Control verified | Strict schemas and tested malformed-input defenses | An `owner` field and invalid payloads were rejected; content type, field length, request size, and UUID cases returned the expected error codes. |
| F-04 · Control verified | Login limiting in app tests and the corrected local launch | Five attempts were allowed; the next was limited with `429` and `Retry-After`. A fake clock verified window expiry. |
| F-05 · Configuration issue corrected for local demo | Initial live launch exposed a forwarded-header/rate-limit interaction | With default Uvicorn proxy-header handling, the check returned `401` instead of `429`. Starting with `--no-proxy-headers` made the same check return `429`; the live demo then passed. Before/after output is in `docs/evidence/xff-before-after.txt`. |
| F-06 · Control verified | The health endpoint exposes only its status field in the tested response | `GET /health` returned exactly `{"status":"ok"}`; a focused regression test now guards the response shape. |

**F-05 analysis and disposition.** The limiter keys on the address supplied by the ASGI request and does not read `X-Forwarded-For` itself. In the first live run, Uvicorn's default proxy-header behavior caused the forged forwarding value to be used as the apparent client address, so repeated requests were not grouped under the expected rate-limit key. `TestClient` did not exercise this server configuration. For the local-only demo, proxy-header handling was disabled; in a real proxy deployment, only the actual trusted proxy should be configured. This was corrected in the launch command, not by changing application code. Uvicorn's official settings describe proxy-header handling and the default trusted loopback addresses [20].

## 7. Limitations and residual risks

- **In-memory state:** users, tickets, and rate-limit counters reset on restart and are not shared across worker processes. This is unsuitable for durable data or a multi-worker deployment.
- **Body-size boundary:** the configured limit rejects declared `Content-Length` values above 10 KiB. A chunked body without that header is not capped by this middleware check.
- **Rate-limit topology:** clients sharing an address share a quota, and a per-process, address-based counter is not a distributed abuse-control system.
- **Token lifecycle:** access tokens last 15 minutes, but there is no refresh flow or revocation mechanism. A valid token can remain usable until expiry or account disablement.
- **Signing-key lifecycle:** a random key is generated if `APP_SECRET_KEY` is unset; those tokens stop working after restart. A configured key must be at least 32 characters. Rotation and persistent secret management are not implemented.
- **Transport and deployment:** the demonstrated service uses HTTP on loopback. TLS, remote deployment, proxy allow-list configuration, and multi-worker behavior were not tested.
- **Test and mutation scope:** the suite verifies selected requirements and detects the five inserted weaknesses. It does not prove that all vulnerabilities or edge cases have been found.

## 8. Recommended next steps

| Priority | Recommendation | Reason |
|---|---|---|
| Before any broader deployment | Keep the service loopback-only unless a separately reviewed deployment design is approved; configure proxy trust explicitly | The demonstration is not designed or tested as a public service |
| High | Enforce body limits while reading the request stream, in addition to validating `Content-Length` | The current middleware cannot cap a chunked body that omits that header |
| High | Add a real-Uvicorn integration test for forwarded-address and rate-limit behavior | The in-process client did not reproduce the observed launch-configuration interaction |
| Medium | Use persistent storage and a shared rate-limit backend if multiple processes are introduced | Current in-memory state is process-local and resets on restart |
| Medium | Define token revocation and signing-key rotation procedures | Current access tokens remain valid until expiry or account disablement |
| Further verification | Run dependency review and additional authorized local-lab testing | Neither activity was performed for this report; results must be recorded only if actually completed |

## 9. Use of AI tools

Claude and GitHub Copilot helped draft code and documents. I ran and reviewed the project.

## 10. Sources and supporting evidence

Bracketed source numbers refer to `references.md`, which records titles, URLs, access-date notes, and how each source was used. The WSTG citation now points to the current official authorization-testing section. The Uvicorn website could not be reached from this environment, so its official settings file on GitHub is cited instead.

Primary project evidence:

- Automated run: `docs/evidence/pytest-output.txt`
- Live requests: `docs/evidence/demo-output.txt`
- Mutation results: `docs/evidence/mutation-check-output.txt` and `docs/evidence/mutation-results.json`
- Before/after launch behavior: `docs/evidence/xff-before-after.txt`
- Expected/actual matrix: `docs/test-matrix.md`
- Scope and synthetic data: `docs/scope-and-ethics.md`
