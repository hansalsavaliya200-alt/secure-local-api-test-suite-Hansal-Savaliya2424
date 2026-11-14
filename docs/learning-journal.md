# Learning journal: Hansal Savaliya, Intern ID 2424

**Task 2 title:** Build a secure local API and test suite. **Group A:** Ethical Hacking & Web Application Security. All testing was done on my own computer against my own local API with fictional data.

## 1. Verification work

I ran the automated suite and recorded **119 passing test cases across 78 test functions**. It covers successful requests as well as rejected logins, invalid tokens, access-control failures, invalid input and boundary cases. The saved output is in [pytest-output.txt](evidence/pytest-output.txt), and the selected expected-versus-actual cases are in the [test matrix](test-matrix.md).

I also ran the mutation check. Five selected controls were weakened in temporary copies of the code, and the suite detected all five changes. The unmodified code passed its retest. This shows the tests catch those particular regressions. It does not prove that every possible security issue is covered. See [mutation-check-output.txt](evidence/mutation-check-output.txt) and [mutation-results.json](evidence/mutation-results.json).

The local demo against `127.0.0.1:8011` exercised authentication, ticket access, input validation, role checks and rate limiting. Its saved output ends with **ALL CHECKS PASSED** ([demo-output.txt](evidence/demo-output.txt)).

## 2. Concepts I learned

### Authentication vs authorisation
Authentication asks "who are you?" and authorisation asks "what are you allowed to do?". In the demo, `/me` without a token returned `401` (not authenticated). A normal user listing all accounts returned `403` (authenticated, but not allowed), while the admin got `200`. The API checks in order: the token first, then the role, then the specific object.

### JWT validation
A signed token lets the server detect changes, but only if it verifies the token strictly. My API pins the algorithm to HS256 and requires the `exp`, `iat`, `sub` and `iss` claims ([security.py](../app/security.py)). That rejects an unsigned `alg=none` token and a token that never expires. The algorithm confusion lab showed me what happens when a server lets the token choose its own algorithm.

### Roles and object ownership (IDOR)
The token only identifies the user. The API reads the role from the server on every request, so a changed role applies at once and a client cannot claim one. When a user asks for someone else's ticket, the API returns `404` rather than `403`, so an attacker cannot tell which ticket IDs exist. A requested ID is not proof of permission, which is the point of the "User ID controlled by request parameter" lab.

### Input validation and mass assignment
The API accepts only the fields it expects. An unknown `owner` field and an empty title returned `422`, and form data instead of JSON returned `415`. Rejecting unknown fields blocks mass assignment, where a client adds a field such as a role or a discount that the server then trusts. The role-modification and mass-assignment labs showed this clearly, and my models use `extra="forbid"` ([models.py](../app/models.py)).

### Rate limiting and proxy headers
The 6th login attempt in the demo returned `429` with `Retry-After: 60`. The limiter identifies a client by its real connection address, because a header such as `X-Forwarded-For` is controlled by the client. The brute-force lab showed how a weak limit can be sidestepped, so my limiter counts every login attempt whether or not the password is correct and never resets on success.

### Mutation testing
Passing tests only show that the code meets the tests. By removing a control on purpose, such as the admin check or the ownership check, I could confirm that the tests fail when a control is missing. This makes the test suite itself more trustworthy, but it only covers the five changes I tried.

## 3. Mistakes and troubleshooting

### Mistake 1: the forwarded-address check returned `401` instead of `429`

**What happened:** in a live check against the running server, the forged `X-Forwarded-For` request after the login limit returned `401` where I expected `429`. My unit tests had not caught this.

**How I diagnosed it:** I compared two runs of the same check, one with Uvicorn's default settings and one started with `--no-proxy-headers`. The first failed and the second passed. This pointed to Uvicorn's proxy-header handling and not to my limiter code. The before-and-after output is in [xff-before-after.txt](evidence/xff-before-after.txt).

**What I changed:** I started Uvicorn with `--no-proxy-headers`, and the README now says to do so. The check then returned `429` and the demo passed.

**What I learned:** a control can be correct in the application code and still be undone by how the server is started. My unit tests do not go through Uvicorn, so a live test against the running server is also needed.

### Mistake 2: the API would not start on port 8000

**What happened:** starting the API on port `8000` returned Windows `WinError 10013`.

**What I did:** I used port `8011` for the API and the demo, which then ran successfully. The recorded evidence does not show why Windows denied the original bind, so I have not assumed a cause.

**What I would do next time:** check which process or reserved range is using the port before changing it, so I know the cause and not just the workaround.

The six completed labs and their individual connections to the API are documented in the [PortSwigger lab log](portswigger-lab-log.md). The concepts above summarize the controls those labs relate to without repeating the lab entries.
