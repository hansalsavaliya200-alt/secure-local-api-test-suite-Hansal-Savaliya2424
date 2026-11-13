"""Rate limiting: allowed, denied, reset and bypass attempts."""
from fastapi.testclient import TestClient


def bad_login(client):
    return client.post("/auth/login", json={"username": "alice", "password": "wrong-password"})


def test_login_is_limited_after_five_attempts(client):
    codes = [bad_login(client).status_code for _ in range(7)]
    assert codes == [401] * 5 + [429] * 2


def test_429_has_retry_after_and_standard_error_shape(client):
    for _ in range(5):
        bad_login(client)
    response = bad_login(client)
    assert response.status_code == 429
    assert 1 <= int(response.headers["retry-after"]) <= 60
    assert response.json()["error"]["code"] == "rate_limited" and response.json()["error"]["request_id"]


def test_correct_password_is_also_blocked_while_limited(client):
    for _ in range(5):
        bad_login(client)
    good = client.post("/auth/login", json={"username": "alice", "password": "alice-demo-Passw0rd!"})
    assert good.status_code == 429


def test_limit_resets_after_the_window(client, clock):                          # edge case
    for _ in range(6):
        bad_login(client)
    clock.advance(30)
    assert bad_login(client).status_code == 429          # still inside the 60 second window
    clock.advance(31)
    assert bad_login(client).status_code == 401          # window has passed


def test_one_client_does_not_block_another(app, client):
    for _ in range(6):
        bad_login(client)
    other = TestClient(app, client=("10.9.9.9", 5000), raise_server_exceptions=False)
    assert bad_login(other).status_code == 401


def test_forged_forwarding_header_cannot_bypass_the_limit(client):
    codes = [client.post("/auth/login", json={"username": "alice", "password": "wrong-password"},
                         headers={"X-Forwarded-For": f"10.1.1.{i}"}).status_code for i in range(8)]
    assert codes[:5] == [401] * 5 and 429 in codes[5:]


def test_general_limit_is_sixty_per_minute(client):
    assert all(client.get("/health").status_code == 200 for _ in range(60))
    assert client.get("/health").status_code == 429


def test_login_limit_does_not_block_other_endpoints(client, auth):
    for _ in range(6):
        bad_login(client)
    assert client.get("/me", headers=auth("alice")).status_code == 200
