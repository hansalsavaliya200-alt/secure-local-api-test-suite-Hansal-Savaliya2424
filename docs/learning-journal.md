# Learning journal: Hansal Savaliya, Intern ID 2424

## What I ran and what I saw

- I ran the pytest suite. The saved output shows **119 passed** ([pytest-output.txt](evidence/pytest-output.txt)).
- I ran the mutation check. All **5** weakened controls were detected, and the unmodified code passed the retest ([mutation-check-output.txt](evidence/mutation-check-output.txt)).
- I ran the demo against my local server on `127.0.0.1:8011`. It ended with **ALL CHECKS PASSED** ([demo-output.txt](evidence/demo-output.txt)).
- Starting the API on port `8000` failed on Windows with `WinError 10013`, so I used port `8011` instead. I have not confirmed why Windows refused port 8000.
- The forwarded-address check failed at first: it expected `429` but got `401` with Uvicorn's default proxy-header handling. After I started Uvicorn with `--no-proxy-headers` it returned `429` ([xff-before-after.txt](evidence/xff-before-after.txt)).

## Concepts I learned

### 1. Authentication vs authorisation
What I saw: `/me` without a token gave `401`; a normal user listing all accounts gave `403`; the admin got `200`.

**In my own words, what is the difference, and where in the request does each one happen?**
`<WRITE 2-3 SENTENCES>`

### 2. JWT validation
What I saw: a modified token gave `401`. The tests also cover an `alg=none` token and an expired one. The API pins HS256 and requires `exp`, `iat`, `sub` and `iss` ([security.py](../app/security.py)).

**Why does the server pin the algorithm instead of reading it from the token?**
`<WRITE 2-3 SENTENCES>`

### 3. Role checks and ticket ownership
What I saw: Bob asking for Alice's ticket gave `404`; the agent could read it.

**Why `404` and not `403`? Why is the role read from the server and not from the token?**
`<WRITE 2-3 SENTENCES>`

### 4. Input validation
What I saw: an unknown `owner` field and an empty title gave `422`; form data instead of JSON gave `415` ([models.py](../app/models.py), [test-matrix.md](test-matrix.md)).

**What attack does rejecting unknown fields stop?**
`<WRITE 2-3 SENTENCES>`

### 5. Rate limiting and proxy headers
What I saw: the 6th login attempt gave `429` with `Retry-After: 60`.

**How does the limiter decide who a client is, and why can't it trust `X-Forwarded-For`?**
`<WRITE 2-3 SENTENCES>`

### 6. Mutation testing
What I saw: removing 5 controls in temporary copies made tests fail every time, and the real code passed the retest. This shows the suite catches those 5 changes, not every possible bug ([mutation-results.json](evidence/mutation-results.json)).

**What does this prove that "116/119 tests pass" alone does not?**
`<WRITE 2-3 SENTENCES>`

## A mistake I ran into

**What happened:** the port 8000 error and the `401` instead of `429` result (see above).

**How I diagnosed it:** `<WHAT DID YOU LOOK AT? e.g. the error text, the server log, what you tried next>`

**What I changed:** port 8011, and `--no-proxy-headers`.

**What I would do differently:** `<YOUR ANSWER. Don't guess the cause of the port error if you didn't confirm it.>`

## PortSwigger labs

My lab records are in [portswigger-lab-log.md](portswigger-lab-log.md).

**What did the labs change in how I look at my own API?**
`<WRITE 2-3 SENTENCES>`
