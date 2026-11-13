# Learning journal: Hansal Savaliya, Intern ID 2424

## What I did and observed

- I ran the pytest suite; the saved output shows **119 passed**. See [pytest-output.txt](evidence/pytest-output.txt).
- I ran the mutation check. The recorded results show that all **five** weakened controls were detected and that the unmodified code passed its retest. See [mutation-check-output.txt](evidence/mutation-check-output.txt).
- I ran the local demo against `127.0.0.1:8011`. It checked authentication, ticket access, input validation, role restrictions, and rate limiting, and ended with **ALL CHECKS PASSED**. See [demo-output.txt](evidence/demo-output.txt).
- When I first tried to start the API on port `8000`, Windows returned `WinError 10013`. I used port `8011` for the API and demo instead. The recorded results show that the demo then passed; they do not establish why Windows denied the first bind.
- A separate before-and-after run checked forwarded client addresses. With Uvicorn's default proxy-header handling, the check expected `429` but received `401`. After starting Uvicorn with `--no-proxy-headers`, it received `429`. The recorded output is [xff-before-after.txt](evidence/xff-before-after.txt).

## Security concepts I tested

### 1. Authentication and authorization

In the demo, a request to `/me` without a token returned `401`. A user trying to list all accounts received `403`, while the admin request succeeded. The results show authentication and permission checks at different points in a request.

**What I took from this:** `<ADD YOUR OWN TAKEAWAY>`

### 2. JWT validation

The demo rejected a modified token with `401`. The test suite also checks an unsigned `alg=none` token and an expired token. The API pins HS256 and requires the `exp`, `iat`, `sub`, and `iss` claims; see [security.py](../app/security.py).

**What I took from this:** `<ADD YOUR OWN TAKEAWAY>`

### 3. Role and ticket-ownership checks

In the recorded demo, Bob's request for Alice's ticket returned `404`, while the authorized agent could read it. The tests also check that users cannot perform admin-only actions.

**What I took from this:** `<ADD YOUR OWN TAKEAWAY>`

### 4. Input validation

The demo received `422` for an unknown `owner` field and an empty title, and `415` for form data instead of JSON. The test suite also checks field boundaries and oversized request bodies. These checks are defined in [models.py](../app/models.py) and summarized in [test-matrix.md](test-matrix.md).

**What I took from this:** `<ADD YOUR OWN TAKEAWAY>`

### 5. Rate limiting and proxy headers

The sixth login attempt in the demo received `429` with a `Retry-After` value of 60 seconds. The before-and-after record also shows why the Uvicorn launch configuration mattered for the forwarded-address check.

**What I took from this:** `<ADD YOUR OWN TAKEAWAY>`

### 6. Mutation testing

The mutation run weakened five controls in temporary copies. Each change caused relevant tests to fail, and the unmodified code passed its retest. This demonstrates that the suite detects those selected changes; it does not prove that every possible defect is covered. See [mutation-results.json](evidence/mutation-results.json).

**What I took from this:** `<ADD YOUR OWN TAKEAWAY>`

## Troubleshooting reflection

The recorded port issue and proxy-header check above are real project events. The files document the observed errors and the configuration changes that produced passing demo checks.

**My diagnosis and lesson:** `<IN YOUR OWN WORDS, describe what you checked, why you chose the workaround, and what you would do differently next time. Do not guess why Windows denied port 8000 if you did not confirm the cause.>`

## PortSwigger reflection

The confirmed lab records are in [portswigger-lab-log.md](portswigger-lab-log.md). Add your personal takeaways there in your own words.
