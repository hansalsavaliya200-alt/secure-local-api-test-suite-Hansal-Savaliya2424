"""Walks through allowed and denied requests against the RUNNING local API (standard library only).

Start the server first (see README), then in a second terminal:  python scripts/demo_requests.py
Every line shows: who called what, the status we expected, the status we got, and PASS/FAIL.
Local use only: it talks to 127.0.0.1 and uses the fictional demo accounts.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
PASSWORDS = {name: f"{name}-demo-Passw0rd!" for name in ("alice", "bob", "carol", "dave")}
failures = 0


def call(method, path, token=None, body=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    request = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read().decode()
            return response.status, (json.loads(text) if text else None), response.headers
    except urllib.error.HTTPError as error:
        text = error.read().decode()
        return error.code, (json.loads(text) if text else None), error.headers


def check(label, expected, result):
    global failures
    status = result[0]
    verdict = "PASS" if status == expected else "FAIL"
    failures += verdict == "FAIL"
    print(f"  [{verdict}] {label:<62} expected {expected}, got {status}")
    return result


def login(name):
    status, body, _ = call("POST", "/auth/login", body={"username": name, "password": PASSWORDS[name]})
    assert status == 200, f"login failed for {name}: {status}"
    return body["access_token"]


print(f"Target: {BASE}\n")
print("1. Public and unauthenticated")
check("GET /health (public)", 200, call("GET", "/health"))
check("GET /me with no token", 401, call("GET", "/me"))
check("GET /me with a tampered token", 401, call("GET", "/me", token="eyJhbGciOiJIUzI1NiJ9.e30.tampered"))

print("\n2. Log in as each fictional role (tokens are not printed)")
tokens = {name: login(name) for name in PASSWORDS}
print("  got tokens for: alice (user), bob (user), carol (agent), dave (admin)")

print("\n3. Input validation")
status, ticket, _ = check("alice creates a valid ticket", 201, call("POST", "/tickets", tokens["alice"],
                          {"title": "Laptop will not boot", "description": "Black screen", "priority": "high"}))
ticket_id = ticket["id"]
check("alice sends an unknown field (owner=dave)", 422, call("POST", "/tickets", tokens["alice"], {"title": "x", "owner": "dave"}))
check("alice sends an empty title", 422, call("POST", "/tickets", tokens["alice"], {"title": ""}))
check("alice sends a 101-character title", 422, call("POST", "/tickets", tokens["alice"], {"title": "a" * 101}))
check("alice sends invalid JSON", 422, call("POST", "/tickets", tokens["alice"], raw=b"{broken"))
check("alice sends form data instead of JSON", 415, call("POST", "/tickets", tokens["alice"], raw=b"title=x",
      headers={"Content-Type": "application/x-www-form-urlencoded"}))

print("\n4. Object-level access (who owns the ticket?)")
check("bob reads alice's ticket", 404, call("GET", f"/tickets/{ticket_id}", tokens["bob"]))
check("alice reads her own ticket", 200, call("GET", f"/tickets/{ticket_id}", tokens["alice"]))
check("carol (agent) reads alice's ticket", 200, call("GET", f"/tickets/{ticket_id}", tokens["carol"]))

print("\n5. Role checks")
check("alice (user) lists all accounts", 403, call("GET", "/admin/users", tokens["alice"]))
check("carol (agent) lists all accounts", 403, call("GET", "/admin/users", tokens["carol"]))
check("dave (admin) lists all accounts", 200, call("GET", "/admin/users", tokens["dave"]))
check("alice changes ticket status", 403, call("PATCH", f"/tickets/{ticket_id}/status", tokens["alice"], {"status": "closed"}))
check("carol (agent) changes ticket status", 200, call("PATCH", f"/tickets/{ticket_id}/status", tokens["carol"], {"status": "in_progress"}))
check("alice makes herself admin", 403, call("PATCH", "/admin/users/alice/role", tokens["alice"], {"role": "admin"}))
check("carol (agent) deletes a ticket", 403, call("DELETE", f"/tickets/{ticket_id}", tokens["carol"]))
check("dave (admin) deletes the ticket", 204, call("DELETE", f"/tickets/{ticket_id}", tokens["dave"]))
check("deleted ticket is gone", 404, call("GET", f"/tickets/{ticket_id}", tokens["dave"]))

print("\n6. Rate limiting (login allows 5 attempts per minute per client; 4 were used in step 2)")
bad = {"username": "alice", "password": "wrong-password"}
check("wrong password, attempt 5 of 5", 401, call("POST", "/auth/login", body=bad))
status, body, headers = check("wrong password, attempt 6 (over the limit)", 429, call("POST", "/auth/login", body=bad))
print(f"       Retry-After: {headers.get('Retry-After')} seconds, error code: {body['error']['code']}")
check("forged X-Forwarded-For does not bypass the limit", 429,
      call("POST", "/auth/login", body=bad, headers={"X-Forwarded-For": "203.0.113.9"}))

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
sys.exit(1 if failures else 0)
