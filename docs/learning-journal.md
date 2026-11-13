# Learning journal: Hansal Savaliya, Intern ID 2424

> AI-assisted draft based on the project code, tests, and recorded verification. Review it before submission and change any first-person reflection that does not match your own understanding or experience.

## Concepts learned (at least 5)

### 1. Authentication vs authorisation
**AI-drafted note for you to review and rewrite:** Authentication checks who is making a request; authorisation checks what that authenticated user is allowed to do. In this API, bearer-token verification authenticates a user, while role and ownership checks decide which routes and tickets that user may access.

### 2. JWT and why the algorithm is pinned
**AI-drafted note for you to review and rewrite:** This API accepts HS256 tokens and requires the `exp`, `iat`, `sub`, and `iss` claims. Pinning the algorithm and checking the required claims prevents accepting unsigned or incorrectly formed tokens; the issuer is also checked.

### 3. Role-based access control and object-level access (IDOR)
**AI-drafted note for you to review and rewrite:** Role checks limit which actions a user can take, while ownership checks limit which individual tickets a user can access. Returning the same 404 for another user's ticket and a missing ticket avoids confirming whether that ticket exists.

### 4. Input validation and mass assignment
**AI-assisted draft for you to review:** The API validates ticket fields for type, length, allowed values, and disallowed control characters. It also rejects unknown fields such as `owner`, so a client cannot choose who owns a ticket by adding an extra property to the request. The tests check both boundary values and rejected payloads.

### 5. Rate limiting and why `X-Forwarded-For` cannot be trusted
**AI-assisted draft for you to review:** The login endpoint permits five attempts in a 60-second window and then returns `429` with a `Retry-After` header. The live test also showed that rate limiting depends on server configuration: for this local run, Uvicorn's proxy-header handling caused a forged `X-Forwarded-For` value to appear as a different client. Forwarded addresses should only be trusted from a correctly configured proxy.

### 6. (Optional) Mutation testing
**AI-assisted draft for you to review:** Mutation testing checks whether tests notice when a security control is weakened. In this project, five weaknesses were introduced in temporary copies; the test suite detected all five, and the unmodified project passed its retest. This provides evidence that the selected tests catch those specific regressions, not proof that every possible flaw has been found.

## A real failure in the recorded project run

> This entry is based on the recorded live run. Keep it as your personal reflection only if it matches what you experienced; otherwise revise it.

**What failed:** The live demo's forwarded-address check expected `429` but received `401` when the API was started with Uvicorn's default proxy-header handling.

**Diagnosis recorded:** The server treated the client-supplied `X-Forwarded-For` value as the request address. Changing that header made requests appear to come from different clients to the address-based limiter, so the expected limit was not reached.

**What changed:** The local demo server was restarted with `--no-proxy-headers`. The same check then returned `429`, and the live demo passed. No application code was changed to obtain this result.

**Follow-up lesson (AI-assisted draft):** Include the real server launch configuration in end-to-end checks early. The in-process test client did not expose this Uvicorn-specific behavior.

## PortSwigger labs

`<WRITE YOUR OWN SUMMARY AFTER PROVIDING YOUR REAL LAB DETAILS>`
