"""Role checks (user / agent / admin) and object-level access. Allowed and denied cases."""
import uuid

import pytest


# ---- admin-only endpoints ------------------------------------------------------------------
@pytest.mark.parametrize("who,expected", [("alice", 403), ("carol", 403), ("dave", 200)])
def test_admin_users_list_by_role(client, auth, who, expected):
    assert client.get("/admin/users", headers=auth(who)).status_code == expected


def test_admin_users_requires_authentication(client):
    assert client.get("/admin/users").status_code == 401


def test_admin_user_list_never_contains_password_hashes(client, auth):
    body = client.get("/admin/users", headers=auth("dave")).text
    assert "scrypt$" not in body and "password" not in body


@pytest.mark.parametrize("who,expected", [("alice", 403), ("carol", 403), ("dave", 204)])
def test_delete_ticket_is_admin_only(client, auth, make_ticket, who, expected):
    ticket = make_ticket("alice")
    assert client.delete(f"/tickets/{ticket['id']}", headers=auth(who)).status_code == expected


def test_deleted_ticket_is_gone(client, auth, make_ticket):
    ticket = make_ticket("alice")
    client.delete(f"/tickets/{ticket['id']}", headers=auth("dave"))
    assert client.get(f"/tickets/{ticket['id']}", headers=auth("dave")).status_code == 404


# ---- agent actions ------------------------------------------------------------------------
@pytest.mark.parametrize("who,expected", [("alice", 403), ("carol", 200), ("dave", 200)])
def test_status_change_by_role(client, auth, make_ticket, who, expected):
    ticket = make_ticket("alice")
    response = client.patch(f"/tickets/{ticket['id']}/status", json={"status": "in_progress"}, headers=auth(who))
    assert response.status_code == expected


def test_owner_cannot_close_own_ticket(client, auth, make_ticket):
    ticket = make_ticket("alice")
    response = client.patch(f"/tickets/{ticket['id']}/status", json={"status": "closed"}, headers=auth("alice"))
    assert response.status_code == 403


def test_closed_ticket_cannot_be_reopened(client, auth, make_ticket):          # edge case
    ticket = make_ticket("alice")
    url = f"/tickets/{ticket['id']}/status"
    assert client.patch(url, json={"status": "closed"}, headers=auth("carol")).status_code == 200
    assert client.patch(url, json={"status": "open"}, headers=auth("carol")).status_code == 409


def test_invalid_status_value_is_rejected(client, auth, make_ticket):
    ticket = make_ticket("alice")
    response = client.patch(f"/tickets/{ticket['id']}/status", json={"status": "deleted"}, headers=auth("carol"))
    assert response.status_code == 422


# ---- object-level access (who owns the ticket?) ---------------------------------------------
def test_user_sees_only_own_tickets(client, auth, make_ticket):
    make_ticket("alice", title="Alice extra")
    items = client.get("/tickets", headers=auth("bob")).json()["items"]
    assert items and all(t["owner"] == "bob" for t in items)


@pytest.mark.parametrize("who", ["carol", "dave"])
def test_agent_and_admin_see_all_tickets(client, auth, who):
    assert client.get("/tickets", headers=auth(who)).json()["total"] == 2


def test_owner_can_read_own_ticket(client, auth, make_ticket):
    ticket = make_ticket("alice")
    assert client.get(f"/tickets/{ticket['id']}", headers=auth("alice")).status_code == 200


def test_user_cannot_read_another_users_ticket(client, auth, make_ticket):
    ticket = make_ticket("alice")
    assert client.get(f"/tickets/{ticket['id']}", headers=auth("bob")).status_code == 404


def test_agent_can_read_any_ticket(client, auth, make_ticket):
    ticket = make_ticket("alice")
    assert client.get(f"/tickets/{ticket['id']}", headers=auth("carol")).status_code == 200


def test_foreign_ticket_and_missing_ticket_look_identical(client, auth, make_ticket):
    ticket = make_ticket("alice")
    foreign = client.get(f"/tickets/{ticket['id']}", headers=auth("bob")).json()["error"]
    missing = client.get(f"/tickets/{uuid.uuid4()}", headers=auth("bob")).json()["error"]
    assert foreign["code"] == missing["code"] and foreign["message"] == missing["message"]


def test_owner_is_taken_from_token_not_body(client, auth):
    response = client.post("/tickets", json={"title": "x", "owner": "dave"}, headers=auth("alice"))
    assert response.status_code == 422                                  # mass assignment refused
    created = client.post("/tickets", json={"title": "x"}, headers=auth("alice")).json()
    assert created["owner"] == "alice"


# ---- privilege escalation ----------------------------------------------------------------------
def test_user_cannot_make_themselves_admin(client, auth, app):
    response = client.patch("/admin/users/alice/role", json={"role": "admin"}, headers=auth("alice"))
    assert response.status_code == 403
    assert app.state.store.users["alice"].role == "user"


def test_admin_can_change_a_role(client, auth, app):
    response = client.patch("/admin/users/bob/role", json={"role": "agent"}, headers=auth("dave"))
    assert response.status_code == 200 and app.state.store.users["bob"].role == "agent"


def test_admin_cannot_remove_own_admin_role(client, auth):                    # edge case: lock-out
    response = client.patch("/admin/users/dave/role", json={"role": "user"}, headers=auth("dave"))
    assert response.status_code == 409


@pytest.mark.parametrize("payload", [{"role": "root"}, {"role": ""}, {"role": 1}, {}, {"role": "user", "x": 1}])
def test_invalid_role_values_are_rejected(client, auth, payload):
    assert client.patch("/admin/users/bob/role", json=payload, headers=auth("dave")).status_code == 422


def test_role_change_for_unknown_user_is_404(client, auth):
    assert client.patch("/admin/users/ghost/role", json={"role": "user"}, headers=auth("dave")).status_code == 404
