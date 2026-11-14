# Learning journal: Hansal Savaliya, Intern ID 2424

## Verification work

I ran the automated suite and recorded **119 passing test cases across 78 test functions**. The suite covered successful requests as well as rejected logins, invalid tokens, access-control failures, invalid input, and boundary cases. The saved output is in [pytest-output.txt](evidence/pytest-output.txt), and the selected expected-versus-actual cases are in the [security verification matrix](test-matrix.md).

I also ran the mutation check. Five selected controls were weakened in temporary copies, and the test suite detected all five changes. The unmodified code passed its retest. This showed that the tests catch those particular regressions; it does not prove that every possible security issue is covered. The run is recorded in [mutation-check-output.txt](evidence/mutation-check-output.txt) and [mutation-results.json](evidence/mutation-results.json).

The local demo against `127.0.0.1:8011` exercised authentication, ticket access, input validation, role checks, and rate limiting. Its saved output ends with **ALL CHECKS PASSED** ([demo-output.txt](evidence/demo-output.txt)).

## What the PortSwigger labs connected to the project

The six labs I completed are recorded in the [PortSwigger lab log](portswigger-lab-log.md). Comparing them with this API helped me connect the lab lessons to specific controls and tests:

1. **Username enumeration:** Different login responses can reveal whether a username exists. My API returns the same generic `401` response for an unknown user and an incorrect password (`test_unknown_user_and_wrong_password_look_identical`).
2. **Broken brute-force protection:** A login limit should not be easy to reset or bypass. My API counts unsuccessful and successful attempts during the limit window, and the tests check that a forged `X-Forwarded-For` value does not bypass the limit (`test_correct_password_is_also_blocked_while_limited`, `test_forged_forwarding_header_cannot_bypass_the_limit`).
3. **JWT algorithm confusion:** The server should select the accepted signing algorithm instead of trusting the token header. My API pins HS256 and requires its expected claims. It uses a shared secret and has no public-key/JWKS endpoint, so the exact lab setup is not present in this project (`test_unsigned_alg_none_token_is_refused`, `test_tampered_token_is_401`).
4. **Changing a role through a profile request:** Privileges must be controlled by the server, not assigned from an untrusted request. This API looks up roles on the server, rejects unknown request fields, and tests that a user cannot promote themselves (`test_role_is_read_from_the_server_not_the_token`, `test_user_cannot_make_themselves_admin`).
5. **Changing a user ID in a request:** A requested object ID is not proof of permission to read that object. The API checks ticket ownership server-side; a foreign ticket and a missing ticket both return `404` (`test_user_cannot_read_another_users_ticket`, `test_foreign_ticket_and_missing_ticket_look_identical`).
6. **Mass assignment:** Request models should accept only intended fields, not client-supplied values that should be set by the server. The API rejects extra fields and takes ticket ownership from the authenticated identity (`test_invalid_ticket_bodies_are_rejected`, `test_owner_is_taken_from_token_not_body`).

Across these labs, the common point was to treat client-controlled values as untrusted. In the API, that means validating tokens and request fields, enforcing roles and ownership on the server, and applying login limits consistently. The tests give evidence for these specific controls, not a guarantee that no other weakness exists.

## Troubleshooting notes

### API port

Starting the API on port `8000` returned Windows `WinError 10013`. I used port `8011` for the API and demo, which then ran successfully. The recorded evidence does not establish why Windows denied the original bind, so I have not assumed a cause.

### Uvicorn proxy-header handling

In a separate live check, Uvicorn's default proxy-header handling caused the forwarded-address rate-limit check to return `401` instead of the expected `429`. Starting Uvicorn with `--no-proxy-headers` made that check return `429`; the live demo then passed. The before-and-after output is in [xff-before-after.txt](evidence/xff-before-after.txt). This was a server launch-configuration issue distinct from the port-binding error.
