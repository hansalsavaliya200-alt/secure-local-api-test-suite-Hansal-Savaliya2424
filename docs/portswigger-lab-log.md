# PortSwigger Web Security Academy: lab log

**Author:** Hansal Savaliya · Intern ID 2424

**Source:** [PortSwigger Web Security Academy](https://portswigger.net/web-security)

**Completion date recorded:** 14 November 2026

The six labs below were recorded as completed in PortSwigger's own lab environment. This log summarizes the security lessons and their relevance to this local API; it does not reproduce lab solution steps. The API comparisons refer only to this repository's implementation and tests.

## Completed labs and project connections

| # | Lab title | Security lesson | Related check in this project |
|---:|---|---|---|
| 1 | Username enumeration via different responses | Different login responses can reveal whether an account exists. | Unknown usernames and incorrect passwords receive the same generic response (`test_unknown_user_and_wrong_password_look_identical`). |
| 2 | Broken brute-force protection, IP block | Login limits should apply consistently and should not be resettable by a successful login or bypassed using an untrusted client-supplied address. | Attempts are counted while limited, and a forged `X-Forwarded-For` value does not bypass the limit (`test_correct_password_is_also_blocked_while_limited`, `test_forged_forwarding_header_cannot_bypass_the_limit`). The local Uvicorn demo disables proxy-header processing. |
| 3 | JWT authentication bypass via algorithm confusion | The server must choose the accepted token algorithm rather than trusting a token's header. | Token verification pins HS256 and requires expected claims. This API uses a shared secret and has no public-key or JWKS endpoint; the lab's specific configuration is not present here (`test_unsigned_alg_none_token_is_refused`, `test_tampered_token_is_401`). |
| 4 | User role can be modified in user profile | Privileged fields must be controlled and validated by the server, not accepted from an ordinary client request. | The role is read from server-side user data and users cannot grant themselves admin access (`test_role_is_read_from_the_server_not_the_token`, `test_user_cannot_make_themselves_admin`). Request models also reject unknown fields. |
| 5 | User ID controlled by request parameter | Access to an object must be checked against the authenticated user's permissions and ownership. | Ticket ownership is checked server-side; a foreign ticket and a missing ticket both return 404 (`test_user_cannot_read_another_users_ticket`, `test_foreign_ticket_and_missing_ticket_look_identical`). |
| 6 | Exploiting a mass assignment vulnerability | Accept only the fields intended for a request; clients should not be able to set server-controlled values by adding extra properties. | Strict request models reject extra fields, and ticket ownership is derived from the authenticated identity (`test_invalid_ticket_bodies_are_rejected`, `test_owner_is_taken_from_token_not_body`). |

## Overall reflection

Across these labs, the recurring theme was to treat client-controlled input as untrusted. In this API, that means checking login responses and request limits, validating tokens with server-selected rules, enforcing permissions and ownership on the server, and rejecting fields the request model does not allow. The related test cases provide evidence for these specific controls; they do not establish that the project is free of every possible vulnerability. See the [security verification matrix](test-matrix.md) for the recorded test results.
