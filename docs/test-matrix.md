# Security verification matrix

**Project:** Build a secure local API and test suite

**Scope:** Local FastAPI demonstration using fictional data and loopback requests only.

This document summarizes representative security tests and the captured verification records. The build script runs pytest and reads its JUnit report; expected outcomes and selected examples are maintained in this script.

## Verification summary

| Check | Recorded result | Evidence source |
|---|---|---|
| Pytest cases | 119 passed, 0 failed, 0 errors, 0 skipped (119 total) | `junit.xml` |
| Test functions | 78 passed, 0 failed (78 functions; parametrized cases grouped) | `junit.xml` |
| Mutation checks | 5 of 5 weakened controls detected | `mutation-results.json` |
| Live demo | All checks passed | `demo-output.txt` |

## Representative test cases

Expected behavior is shown alongside the result for each selected test function. A `PASS` means the function passed in the latest pytest run; parametrized cases are grouped by function.

| # | Class | Scenario | Expected behavior | Latest result | Test function |
|---:|---|---|---|---|---|
| 1 | Positive | Health response exposes only its status field | `{"status":"ok"}` | PASS | `test_health_response_contains_only_status` |
| 2 | Positive | Valid login | 200 and a bearer token | PASS | `test_login_success_returns_bearer_token` |
| 3 | Positive | User reads own ticket | 200 | PASS | `test_owner_can_read_own_ticket` |
| 4 | Positive | Agent/admin change ticket status | 200 for agent and admin | PASS | `test_status_change_by_role` |
| 5 | Positive | Admin deletes a ticket | 204 for admin | PASS | `test_delete_ticket_is_admin_only` |
| 6 | Negative | Wrong password | 401, generic message | PASS | `test_login_wrong_password_is_401` |
| 7 | Negative | No token on a protected route | 401 | PASS | `test_protected_route_without_token_is_401` |
| 8 | Negative | User reads someone else's ticket | 404 (not 403) | PASS | `test_user_cannot_read_another_users_ticket` |
| 9 | Negative | User/agent list accounts | 403 for user and agent | PASS | `test_admin_users_list_by_role` |
| 10 | Negative | Privilege escalation attempt | 403, role unchanged | PASS | `test_user_cannot_make_themselves_admin` |
| 11 | Negative | Modified JWT | 401 | PASS | `test_tampered_token_is_401` |
| 12 | Negative | JWT with alg=none | 401 | PASS | `test_unsigned_alg_none_token_is_refused` |
| 13 | Negative | Expired JWT | 401 | PASS | `test_expired_token_is_401` |
| 14 | Negative | 6th login attempt in 60 s | 429 with Retry-After | PASS | `test_login_is_limited_after_five_attempts` |
| 15 | Negative | Form data instead of JSON | 415 | PASS | `test_wrong_content_type_is_415` |
| 16 | Negative | Unknown field, empty title, wrong types | 422 | PASS | `test_invalid_ticket_bodies_are_rejected` |
| 17 | Boundary | Title of 100 vs 101 characters | 100 accepted, 101 rejected | PASS | `test_title_length_boundaries` |
| 18 | Boundary | Description of 1000 vs 1001 characters | 1000 accepted, 1001 rejected | PASS | `test_description_length_boundaries` |
| 19 | Boundary | Body above the size limit | 413 | PASS | `test_oversized_body_is_413` |
| 20 | Boundary | Chunked body above the size limit without Content-Length | 413 | PASS | `test_chunked_oversized_body_is_413` |
| 21 | Boundary | Ticket ID that is not a UUID | 404, no crash | PASS | `test_malformed_ticket_ids_are_404_not_500` |
| 22 | Boundary | Wait out the 60 s window (fake clock) | Login allowed again | PASS | `test_limit_resets_after_the_window` |
| 23 | Boundary | New X-Forwarded-For on each attempt | Still limited (429) | PASS | `test_forged_forwarding_header_cannot_bypass_the_limit` |
| 24 | Boundary | Last admin demotes themselves | 409 | PASS | `test_admin_cannot_remove_own_admin_role` |
| 25 | Boundary | Role changed after token was issued | New role applies at once | PASS | `test_role_is_read_from_the_server_not_the_token` |

## Mutation test results

Each listed weakness was introduced only in a temporary copy. Detection means at least one test failed under that mutation; the unmodified project was then retested.

| Temporary weakness | Failing tests | Detection result |
|---|---:|---|
| any logged-in user may list all accounts (broken access control) | 2 | Detected |
| any logged-in user may delete tickets (broken access control) | 2 | Detected |
| any logged-in user may read anyone's ticket (IDOR) | 2 | Detected |
| unknown fields such as 'owner' or 'role' are silently accepted (mass assignment) | 4 | Detected |
| unlimited password guessing on the login endpoint | 5 | Detected |

Retest on unmodified code: **PASS** — 119 passed in 3.61s.

## Live-server proxy-header check

| Run | Recorded outcome |
|---|---|
| Initial run with Uvicorn's default proxy-header handling | Forwarded-header rate-limit check failed (expected 429, received 401). |
| Follow-up with `--no-proxy-headers` | Forwarded-header check passed (429). |
| Full demo after the configuration change | All checks passed. |

The demo runs through Uvicorn and covers its proxy-header configuration. FastAPI `TestClient` does not start Uvicorn, so this server-level behavior is recorded separately from the pytest suite.

## Evidence files

- [JUnit report](evidence/junit.xml) — generated by this matrix build.
- [Pytest transcript](evidence/pytest-output.txt) — saved console output from a recorded run.
- [Mutation results](evidence/mutation-results.json) and [mutation transcript](evidence/mutation-check-output.txt).
- [Live demo transcript](evidence/demo-output.txt).
- [Proxy-header before/after transcript](evidence/xff-before-after.txt).

## Evidence provenance

Test counts and outcomes in this matrix are derived from the local JUnit and saved experiment/demo records.
