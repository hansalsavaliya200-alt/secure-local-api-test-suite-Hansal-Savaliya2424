# Learning journal: Hansal Savaliya, Intern ID 2424

> Fill this in **in your own words** as you go. Keep only things that really happened to you. Delete the hints in italics.

## Concepts learned (at least 5)

### 1. Authentication vs authorisation
*What is the difference? Which file shows each? (`app/deps.py`)*

### 2. JWT and why the algorithm is pinned
*What does `alg: none` do? Which test covers it? (`test_unsigned_alg_none_token_is_refused`)*

### 3. Role-based access control and object-level access (IDOR)
*Why does a user get 404, not 403, for someone else's ticket?*

### 4. Input validation and mass assignment
*What happens if the client sends `"owner": "dave"`?*

### 5. Rate limiting and why `X-Forwarded-For` cannot be trusted
*How does a sliding window work? Why does the limiter use the socket address?*

### 6. (Optional) Mutation testing
*What does it prove that a passing test suite alone does not?*

## A mistake or failure (real one)

**What happened:** *Suggested, if it happened to you: the demo client's forged-header check returned 401 instead of 429 when run against uvicorn. If you saw this yourself, say so. If not, write a different real mistake, for example a setup error such as `python` not being found.*

**How I diagnosed it:** *What did you look at? (server log showed the client as `203.0.113.9`.)*

**What I changed:** *`--no-proxy-headers`, and the README note.*

**What I would do differently:**

## PortSwigger labs

*Summary of what the labs taught you. Details go in `portswigger-lab-log.md`.*
