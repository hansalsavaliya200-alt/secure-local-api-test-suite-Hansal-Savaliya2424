# Learning journal: Hansal Savaliya, Intern ID 2424

The notes below summarize concepts used in the project and the recorded verification evidence. They are technical reference material, not personal reflections; the reflection prompts are left for you to complete in your own words.

## Project concepts and technical notes

### 1. Authentication and authorization

Authentication verifies the identity associated with a request; authorization decides which operations that identity may perform. In this API, a valid bearer token establishes the request identity, while route permissions and ticket-ownership checks determine access.

**My reflection:** `<WRITE YOUR OWN EXPLANATION OR EXAMPLE>`

### 2. JWT validation

The API signs access tokens with HS256 and pins that algorithm when verifying them. It requires `exp`, `iat`, `sub`, and `iss`, and validates the issuer. The token carries the user's identity; the role is looked up on the server for each request. See [security.py](../app/security.py).

**My reflection:** `<WRITE WHAT YOU UNDERSTOOD ABOUT TOKEN VALIDATION>`

### 3. Role-based and object-level access control

Role checks constrain actions, while object-level checks constrain access to individual records. This API lets users access their own tickets and returns the same 404 response for another user's ticket as for a missing ticket. A role check by itself would not establish ticket ownership.

**My reflection:** `<WRITE YOUR OWN EXAMPLE OF WHY BOTH CHECKS MATTER>`

### 4. Input validation and mass assignment

The request models reject unknown fields, enforce types and length limits, and reject disallowed control characters. This prevents clients from supplying fields such as `owner` that the server should control. The API also rejects unsupported content types and request bodies above its configured size limit. See [models.py](../app/models.py) and [test-matrix.md](test-matrix.md).

**My reflection:** `<WRITE WHAT INPUT CASE OR TEST YOU FOUND MOST IMPORTANT>`

### 5. Rate limiting and forwarded client addresses

The login route allows five attempts per minute per client and returns `429` with `Retry-After` after the limit is reached. Forwarded-address headers should only be trusted when they come through a configured proxy. The local demo uses Uvicorn's `--no-proxy-headers` option; the recorded initial and follow-up runs are summarized below.

**My reflection:** `<WRITE WHAT YOU LEARNED ABOUT RATE LIMITS OR TRUSTED PROXIES>`

### 6. Mutation testing

Mutation testing checks whether tests detect selected changes that weaken controls. In this project, five changes were made in temporary copies; all five were detected, and the unmodified suite passed its retest. This is evidence about those specific regressions, not proof that every possible defect has been found. See [mutation-results.json](evidence/mutation-results.json).

**My reflection:** `<WRITE WHAT THE MUTATION RESULTS TELL YOU AND WHAT THEY DO NOT>`

## Recorded project issue: local proxy-header behavior

The initial live-demo record shows the forwarded-address rate-limit check expected `429` but received `401` with Uvicorn's default proxy-header handling. The follow-up run used `--no-proxy-headers`; the same check then returned `429`, and the demo passed. The before/after record is in [xff-before-after.txt](evidence/xff-before-after.txt).

**My account of the issue:** `<WRITE WHAT YOU PERSONALLY OBSERVED, HOW YOU DIAGNOSED IT, WHAT YOU CHANGED, AND THE RESULT. If this was not your own experience, describe a real failure you personally encountered instead.>`

## PortSwigger reflection

The confirmed lab records are in [portswigger-lab-log.md](portswigger-lab-log.md). Add your personal takeaways there in your own words.
