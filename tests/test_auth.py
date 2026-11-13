"""Authentication: who are you? Allowed and denied cases."""
import base64
import json
import time

import jwt
import pytest

from app.config import Settings
from app.security import create_token, hash_password, verify_password
from tests.conftest import TEST_SECRET, login


def b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def test_login_success_returns_bearer_token(client):
    response = login(client, "alice")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer" and body["expires_in"] == 900
    assert client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"}).json() == {
        "username": "alice", "role": "user"}


def test_login_wrong_password_is_401(client):
    response = login(client, "alice", "wrong-password")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_unknown_user_and_wrong_password_look_identical(client):
    wrong = login(client, "alice", "wrong-password").json()["error"]
    unknown = login(client, "nobody", "wrong-password").json()["error"]
    assert wrong["message"] == unknown["message"] and wrong["code"] == unknown["code"]


@pytest.mark.parametrize("payload", [
    {}, {"username": "alice"}, {"password": "x"},
    {"username": "alice", "password": 12345},
    {"username": "alice", "password": "x", "role": "admin"},     # extra field
    {"username": "Alice Smith!", "password": "x"},               # bad characters
    {"username": "a" * 33, "password": "x"},                     # too long
    {"username": "alice", "password": "p" * 129},                # too long
])
def test_login_rejects_malformed_bodies(client, payload):
    assert client.post("/auth/login", json=payload).status_code == 422


def test_protected_route_without_token_is_401(client):
    response = client.get("/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("header", ["Basic YWxpY2U6cHc=", "Bearer", "Bearer ", "token abc", "abc"])
def test_malformed_authorization_header_is_401(client, header):
    assert client.get("/me", headers={"Authorization": header}).status_code == 401


def test_tampered_token_is_401(client, auth):
    token = auth("alice")["Authorization"].split()[1]
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    assert client.get("/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401


def test_expired_token_is_401(client, settings):
    token = create_token("alice", settings, ttl_seconds=-10)
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_signed_with_another_key_is_401(client, settings):
    now = int(time.time())
    forged = jwt.encode({"sub": "dave", "iat": now, "exp": now + 900, "iss": settings.issuer},
                        "a-completely-different-secret-key-0123456789", algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_unsigned_alg_none_token_is_refused(client, settings):
    now = int(time.time())
    token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': 'dave', 'iat': now, 'exp': now + 900, 'iss': settings.issuer})}."
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_without_expiry_is_refused(client, settings):
    token = jwt.encode({"sub": "alice", "iat": int(time.time()), "iss": settings.issuer}, TEST_SECRET, algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_with_wrong_issuer_is_refused(client):
    now = int(time.time())
    token = jwt.encode({"sub": "alice", "iat": now, "exp": now + 900, "iss": "someone-else"}, TEST_SECRET, algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_for_unknown_user_is_refused(client, settings):
    token = create_token("ghost", settings)
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_disabled_user_cannot_use_existing_token_or_log_in(client, app, auth):
    header = auth("alice")
    assert client.get("/me", headers=header).status_code == 200
    app.state.store.users["alice"].disabled = True
    assert client.get("/me", headers=header).status_code == 401
    assert login(client, "alice").status_code == 401


def test_role_is_read_from_the_server_not_the_token(client, app, auth):
    """A token issued while carol was an agent must stop working as 'agent' once her role changes."""
    header = auth("carol")
    assert client.get("/tickets", headers=header).json()["total"] == 2   # agent sees everything
    app.state.store.users["carol"].role = "user"
    assert client.get("/tickets", headers=header).json()["total"] == 0   # now only her own


def test_passwords_are_hashed_and_salted(app):
    stored = app.state.store.users["alice"].password_hash
    assert stored.startswith("scrypt$") and "alice-demo-Passw0rd!" not in stored
    assert hash_password("same") != hash_password("same")        # random salt
    assert verify_password("same", hash_password("same"))
    assert not verify_password("other", hash_password("same"))
    assert not verify_password("x", "garbage-not-a-hash")         # damaged hash does not crash


def test_me_does_not_expose_password_hash(client, auth):
    assert set(client.get("/me", headers=auth("alice")).json()) == {"username", "role"}


def test_weak_secret_key_is_rejected_at_startup(monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "short")
    with pytest.raises(ValueError):
        Settings.from_env()
