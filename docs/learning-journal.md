# Learning journal: Hansal Savaliya, Intern ID 2424

The project notes below describe implementation and recorded test evidence. Personal reflections are left for you to complete in your own words.

## Concepts for reflection

### 1. Authentication and authorization

**Project fact:** Authentication verifies the identity associated with a request. Authorization decides what that identity may do. This API verifies bearer tokens before protected requests and applies role and ownership checks to ticket operations.

**My reflection:** `<WRITE YOUR OWN EXPLANATION OR EXAMPLE>`

### 2. JWT validation

**Project fact:** The API signs tokens with HS256, pins that algorithm during verification, and requires the `exp`, `iat`, `sub`, and `iss` claims. The issuer is checked as part of token validation. See [security.py](../app/security.py).

**My reflection:** `<WRITE WHAT YOU UNDERSTOOD ABOUT TOKEN VALIDATION>`

### 3. Role-based and object-level access control

**Project fact:** Roles determine which actions a user may perform; ownership checks determine which ticket records they may access. A user requesting another user's ticket receives the same 404 response as for a missing ticket.

**My reflection:** `<WRITE YOUR OWN EXAMPLE OF WHY BOTH CHECKS MATTER>`

### 4. Input validation and mass assignment

**Project fact:** Request models reject unknown fields, enforce types and length limits, and check text for disallowed control characters. The tests also cover invalid content types and oversized request bodies. See [models.py](../app/models.py) and [test-matrix.md](test-matrix.md).

**My reflection:** `<WRITE WHAT INPUT CASE OR TEST YOU FOUND MOST IMPORTANT>`

### 5. Rate limiting and forwarded client addresses

**Project fact:** Login is limited to five attempts per minute per client, with `429` and `Retry-After` on excess attempts. The local demo uses Uvicorn's `--no-proxy-headers` option so client-supplied forwarding headers do not change the address used by the limiter.

**My reflection:** `<WRITE WHAT YOU LEARNED ABOUT RATE LIMITS OR TRUSTED PROXIES>`

### 6. Mutation testing

**Project fact:** Five security controls were weakened in temporary copies and all five changes were detected by failing tests. The unmodified suite passed its retest. This provides evidence for those specific test cases; it does not prove that the API has no other defects. See [mutation-results.json](evidence/mutation-results.json).

**My reflection:** `<WRITE WHAT THE MUTATION RESULTS TELL YOU AND WHAT THEY DO NOT>`

## Recorded project issue: local proxy-header behavior

The initial live-demo record shows the forwarded-address rate-limit check expected `429` but received `401` with Uvicorn's default proxy-header handling. The follow-up run used `--no-proxy-headers`; the same check then returned `429`, and the demo passed. The before/after record is in [xff-before-after.txt](evidence/xff-before-after.txt).

**My account of the issue:** `<WRITE WHAT YOU PERSONALLY OBSERVED, HOW YOU DIAGNOSED IT, WHAT YOU CHANGED, AND THE RESULT. If this was not your own experience, describe a real failure you personally encountered instead.>`

## PortSwigger reflection

The confirmed lab records are in [portswigger-lab-log.md](portswigger-lab-log.md). Add your personal takeaways there in your own words.
