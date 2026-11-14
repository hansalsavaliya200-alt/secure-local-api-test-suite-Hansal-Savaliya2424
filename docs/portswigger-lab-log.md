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

**What I did and learned:** I used Burp Intruder with a Sniper attack and the provided wordlists to test login attempts. I found a valid username from the difference in the server's responses, then ran the password list against it. A `302` redirect showed a successful login, and I used those credentials to access the account. The lesson is that different login responses reveal which usernames exist, so a login should return the same generic response either way.

**In my API:** login returns the same `401` and message for an unknown user and a wrong password (`test_unknown_user_and_wrong_password_look_identical`). Login is also limited to 5 attempts per minute, which slows password guessing.

## 2. Broken brute-force protection, IP block

**What I did and learned:** The site blocked an IP after 3 failed login attempts. I logged in as `wiener` with the credentials provided, set the Burp resource pool to a maximum of 1 concurrent request, and used a Pitchfork attack to alternate my own valid login with guesses for `carlos`. This let me avoid the block, identify the `carlos` password and log in as him. The lesson is that brute-force protection that can be reset or sidestepped by the client is not reliable, so limits must be enforced on the server and must not be resettable by the attacker.

**In my API:** the limiter counts every login attempt from one client address whether or not the password is correct, and it never resets on a successful login (`test_correct_password_is_also_blocked_while_limited`). It identifies the client by the real connection address, not by the `X-Forwarded-For` header (`test_forged_forwarding_header_cannot_bypass_the_limit`).

## 3. JWT authentication bypass via algorithm confusion

**What I did and learned:** The lab used RSA-signed JWTs. After confirming `/admin` was restricted to the administrator, I retrieved the server's public key from `/jwks.json`, converted it to PEM, Base64-encoded it and used it as a symmetric (HMAC) key. I changed the token's `alg` header to `HS256` and the `sub` claim to `administrator`, then signed it with that key. The server accepted the token, which let me access the admin panel and delete `carlos`. The lesson is that the server must decide which algorithm is allowed and never trust the `alg` value in the token.

**In my API:** `app/security.py` pins `algorithms=["HS256"]` and requires the `exp`, `iat`, `sub` and `iss` claims (`test_unsigned_alg_none_token_is_refused`, `test_tampered_token_is_401`). My API uses a single secret key and has no public key or JWKS endpoint, so this exact attack does not apply to it. The defence is the same idea: the server, not the token, chooses the algorithm.

## 4. User role can be modified in user profile

**What I did and learned:** I logged in as `wiener` and changed the email address, then inspected the request and response in Burp. The response included a `roleid` field. I set `"roleid": 2` in the update request, which gave my account admin access, and I used the admin panel to delete `carlos`. The lesson is that the server must never let a client set fields such as role, and must decide privileges on the server side only.

**In my API:** the role is never taken from the client or the token. It is looked up on the server for every request (`test_role_is_read_from_the_server_not_the_token`), unknown fields are rejected (`test_invalid_ticket_bodies_are_rejected`), and a user cannot make themselves admin (`test_user_cannot_make_themselves_admin`).

## 5. User ID controlled by request parameter

**What I did and learned:** I logged in as `wiener` and noticed that the account page URL contained an `id` parameter. I changed its value from `wiener` to `carlos`, and the server returned Carlos's account page, including his API key. I submitted that key to solve the lab. The lesson is that the server must check that the logged-in user is allowed to access the requested object and must not trust an ID supplied in the request. This flaw is called IDOR (insecure direct object reference), or broken object-level authorisation.

**In my API:** `GET /tickets/{id}` checks the ticket owner against the logged-in user, and the owner comes from the token, never from the request. A ticket that belongs to someone else returns `404`, the same as a missing ticket, so an attacker cannot tell which IDs exist (`test_user_cannot_read_another_users_ticket`, `test_foreign_ticket_and_missing_ticket_look_identical`). The mutation check removed this check and the tests failed (`docs/evidence/mutation-results.json`).

## 6. Exploiting a mass assignment vulnerability

**What I did and learned:** The checkout failed because I did not have enough credit for the jacket. In Burp I saw that the `GET /api/checkout` response included a `chosen_discount` field that the `POST` request did not send. I added `chosen_discount` to the `POST` request. Changing its value to a string caused an error, which showed that the server was processing it. Setting the percentage to `100` let me buy the product for free. The lesson is that the server must accept only the fields it expects and must never let a client set values such as discounts, prices or roles. This flaw is called mass assignment.

**In my API:** the request models use `extra="forbid"`, so an unexpected field such as `owner` or `role` is rejected with `422` (`test_invalid_ticket_bodies_are_rejected`, `test_owner_is_taken_from_token_not_body`). The mutation check changed `forbid` to `ignore` and 4 tests failed.

---

## Overall reflection

Labs 1 and 2 are about login: different responses and weak limits let an attacker guess accounts and passwords. Labs 4, 5 and 6 are about trusting the client: roles, IDs and extra fields must be decided and checked on the server. Lab 3 shows the same rule for tokens: the server decides the algorithm. These are the same checks my API enforces, and I tested each of them with allowed and denied requests (`docs/test-matrix.md`).
