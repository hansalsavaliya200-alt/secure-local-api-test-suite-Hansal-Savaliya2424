# PortSwigger Web Security Academy: lab log

**Author:** Hansal Savaliya, Intern ID 2424
**Source:** PortSwigger Web Security Academy, https://portswigger.net/web-security
**Completed:** 14 November 2026

All labs were done in PortSwigger's own lab environment with Burp Suite, as intended. This log records what each lab showed and how it relates to the controls in my local API (`app/`, `tests/`). Solution steps are not copied here.

## Summary

| # | Topic | Lab | Related control in my API |
|---|-------|-----|---------------------------|
| 1 | Authentication | Username enumeration via different responses | Same `401` for unknown user and wrong password |
| 2 | Authentication | Broken brute-force protection, IP block | Login rate limit, keyed on the real client address |
| 3 | JWT attacks | JWT authentication bypass via algorithm confusion | Pinned algorithm and required claims |
| 4 | Access control | User role can be modified in user profile | Role read from the server, unknown fields rejected |
| 5 | Access control | User ID controlled by request parameter | Ticket ownership check (IDOR) |
| 6 | API testing | Exploiting a mass assignment vulnerability | Strict request models (`extra="forbid"`) |

---

## 1. Username enumeration via different responses

**What I did and learned:** I observed that different login responses can reveal whether a username exists. My takeaway is that login should return the same generic response for an unknown username and an incorrect password.

**In my API:** login returns the same `401` and message for an unknown user and a wrong password (`test_unknown_user_and_wrong_password_look_identical`). Login is also limited to 5 attempts per minute, which slows password guessing.

## 2. Broken brute-force protection, IP block

**What I did and learned:** I observed that the lab's login restriction could be bypassed by alternating successful and unsuccessful attempts. My takeaway is that login limits should be enforced on the server and should count all attempts, not reset after success.

**In my API:** the limiter counts every login attempt from one client address whether or not the password is correct, and it never resets on a successful login (`test_correct_password_is_also_blocked_while_limited`). It identifies the client by the real connection address, not by the `X-Forwarded-For` header (`test_forged_forwarding_header_cannot_bypass_the_limit`).

## 3. JWT authentication bypass via algorithm confusion

**What I did and learned:** The lab demonstrated how accepting a token's algorithm choice can undermine JWT verification. My takeaway is that the server must select the allowed algorithm and validate the token independently of the untrusted header.

**In my API:** `app/security.py` pins `algorithms=["HS256"]` and requires the `exp`, `iat`, `sub` and `iss` claims (`test_unsigned_alg_none_token_is_refused`, `test_tampered_token_is_401`). My API uses a single secret key and has no public key or JWKS endpoint, so this exact attack does not apply to it. The defence is the same idea: the server, not the token, chooses the algorithm.

## 4. User role can be modified in user profile

**What I did and learned:** The lab showed that accepting a client-controlled role field can grant privileges the user should not have. My takeaway is that roles must be assigned and checked by the server.

**In my API:** the role is never taken from the client or the token. It is looked up on the server for every request (`test_role_is_read_from_the_server_not_the_token`), unknown fields are rejected (`test_invalid_ticket_bodies_are_rejected`), and a user cannot make themselves admin (`test_user_cannot_make_themselves_admin`).

## 5. User ID controlled by request parameter

**What I did and learned:** The lab showed that changing a client-controlled identifier could expose another user's information. My takeaway is that the server must check whether the authenticated user is authorized to access each requested object. This flaw is called IDOR (insecure direct object reference), or broken object-level authorisation.

**In my API:** `GET /tickets/{id}` checks the ticket owner against the logged-in user, and the owner comes from the token, never from the request. A ticket that belongs to someone else returns `404`, the same as a missing ticket, so an attacker cannot tell which IDs exist (`test_user_cannot_read_another_users_ticket`, `test_foreign_ticket_and_missing_ticket_look_identical`). The mutation check removed this check and the tests failed (`docs/evidence/mutation-results.json`).

## 6. Exploiting a mass assignment vulnerability

**What I did and learned:** The lab showed that accepting an unexpected client-controlled checkout field could alter the price. My takeaway is that an API should accept only intended fields and keep values such as discounts, prices, and roles under server control. This flaw is called mass assignment.

**In my API:** the request models use `extra="forbid"`, so an unexpected field such as `owner` or `role` is rejected with `422` (`test_invalid_ticket_bodies_are_rejected`, `test_owner_is_taken_from_token_not_body`). The mutation check changed `forbid` to `ignore` and 4 tests failed.

---

## Overall reflection

Labs 1 and 2 are about login: different responses and weak limits let an attacker guess accounts and passwords. Labs 4, 5 and 6 are about trusting the client: roles, IDs and extra fields must be decided and checked on the server. Lab 3 shows the same rule for tokens: the server decides the algorithm. These are the same checks my API enforces, and I tested each of them with allowed and denied requests (`docs/test-matrix.md`).
