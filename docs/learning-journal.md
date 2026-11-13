# Learning journal: Hansal Savaliya, Intern ID 2424

> Review the clearly labeled AI drafts below and rewrite them in your own words. Keep personal claims only if they are true for you.

## Concepts learned (at least 5)

### 1. Authentication vs authorisation
**AI-drafted note for you to review and rewrite:** Authentication checks who is making a request; authorisation checks what that authenticated user is allowed to do. In this API, bearer-token verification authenticates a user, while role and ownership checks decide which routes and tickets that user may access.

### 2. JWT and why the algorithm is pinned
**AI-drafted note for you to review and rewrite:** This API accepts HS256 tokens and requires the `exp`, `iat`, `sub`, and `iss` claims. Pinning the algorithm and checking the required claims prevents accepting unsigned or incorrectly formed tokens; the issuer is also checked.

### 3. Role-based access control and object-level access (IDOR)
**AI-drafted note for you to review and rewrite:** Role checks limit which actions a user can take, while ownership checks limit which individual tickets a user can access. Returning the same 404 for another user's ticket and a missing ticket avoids confirming whether that ticket exists.

### 4. Input validation and mass assignment
`<WRITE YOUR OWN SENTENCE>`

### 5. Rate limiting and why `X-Forwarded-For` cannot be trusted
`<WRITE YOUR OWN SENTENCE>`

### 6. (Optional) Mutation testing
`<WRITE YOUR OWN SENTENCE>`

## A mistake or failure (real one)

**What happened:** `<WRITE A REAL MISTAKE OR FAILURE YOU PERSONALLY EXPERIENCED>`

**How I diagnosed it:** `<WRITE WHAT YOU CHECKED OR OBSERVED>`

**What I changed:** `<WRITE WHAT YOU CHANGED>`

**What I would do differently:** `<WRITE YOUR OWN SENTENCE>`

## PortSwigger labs

`<WRITE YOUR OWN SUMMARY AFTER PROVIDING YOUR REAL LAB DETAILS>`
