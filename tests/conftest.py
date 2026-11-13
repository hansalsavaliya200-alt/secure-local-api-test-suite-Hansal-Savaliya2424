import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.security import create_token
from app.store import DEMO_PASSWORDS

TEST_SECRET = "test-secret-key-0123456789-abcdefghijklmnop"


class FakeClock:
    """Lets rate-limit tests move time forward instantly instead of sleeping."""
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def settings():
    return Settings(secret_key=TEST_SECRET)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def app(settings, clock):
    return create_app(settings, clock=clock)  # fresh store and limiter for every test


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth(app):
    """auth('alice') -> Authorization header. Tokens are minted directly so tests do not
    use up the login rate limit."""
    def _auth(username):
        return {"Authorization": f"Bearer {create_token(username, app.state.settings)}"}
    return _auth


@pytest.fixture
def make_ticket(client, auth):
    def _make(username="alice", **overrides):
        body = {"title": "Cannot log in to VPN", "description": "Error 809 since this morning"}
        body.update(overrides)
        response = client.post("/tickets", json=body, headers=auth(username))
        assert response.status_code == 201, response.text
        return response.json()
    return _make


def login(client, username, password=None):
    return client.post("/auth/login", json={"username": username, "password": password or DEMO_PASSWORDS[username]})
