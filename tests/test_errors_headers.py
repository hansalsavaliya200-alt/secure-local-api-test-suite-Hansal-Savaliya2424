"""Safe errors, security headers, secure defaults and safe logging."""
import logging

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import TEST_SECRET, login


def test_unknown_route_is_generic_404(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found" and "Traceback" not in response.text


def test_wrong_method_is_generic_405(client):
    response = client.put("/health")
    assert response.status_code == 405 and response.json()["error"]["code"] == "method_not_allowed"


def test_unexpected_exception_returns_generic_500(app, auth, make_ticket, monkeypatch):
    ticket = make_ticket("alice")
    monkeypatch.setattr("app.main.public_ticket", lambda t: (_ for _ in ()).throw(RuntimeError("secret internal detail")))
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get(f"/tickets/{ticket['id']}", headers=auth("alice"))
    assert response.status_code == 500
    assert response.json()["error"]["message"] == "Something went wrong."
    assert "secret internal detail" not in response.text and "Traceback" not in response.text
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]


def test_security_headers_are_present(client):
    headers = client.get("/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["cache-control"] == "no-store"
    assert headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert headers["referrer-policy"] == "no-referrer"


def test_every_response_has_a_unique_request_id(client):
    ids = {client.get("/health").headers["x-request-id"] for _ in range(5)}
    assert len(ids) == 5


def test_error_responses_also_carry_security_headers(client):
    response = client.get("/me")
    assert response.status_code == 401 and response.headers["x-content-type-options"] == "nosniff"


def test_interactive_docs_are_disabled_by_default(client):
    assert client.get("/docs").status_code == 404 and client.get("/openapi.json").status_code == 404


def test_docs_can_be_enabled_explicitly_for_local_use(clock):
    docs_app = create_app(Settings(secret_key=TEST_SECRET, enable_docs=True), clock=clock)
    client = TestClient(docs_app, raise_server_exceptions=False)
    assert client.get("/docs").status_code == 200 and client.get("/openapi.json").status_code == 200


def test_logs_never_contain_passwords_or_tokens(client, caplog):
    with caplog.at_level(logging.INFO, logger="secure-api"):
        token = login(client, "alice").json()["access_token"]
        client.get("/me?debug=secret-query", headers={"Authorization": f"Bearer {token}"})
    assert "alice-demo-Passw0rd!" not in caplog.text and token not in caplog.text
    assert "secret-query" not in caplog.text                   # query strings are not logged
    assert "path=/me" in caplog.text and "user=alice" in caplog.text


def test_failed_logins_are_logged_without_credentials(client, caplog):
    with caplog.at_level(logging.INFO, logger="secure-api"):
        client.post("/auth/login", json={"username": "alice", "password": "guess-1234"})
    assert "status=401" in caplog.text and "guess-1234" not in caplog.text
