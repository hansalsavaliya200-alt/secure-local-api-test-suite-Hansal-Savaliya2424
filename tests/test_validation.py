"""Input validation: normal, failure and edge cases."""
import asyncio
import uuid

import httpx
import pytest

JSON = {"Content-Type": "application/json"}


def test_valid_ticket_is_created(client, auth):
    response = client.post("/tickets", json={"title": "Monitor flickers", "description": "Since Monday",
                                             "priority": "high"}, headers=auth("alice"))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "open" and body["priority"] == "high" and body["owner"] == "alice"
    assert set(body) == {"id", "title", "description", "priority", "status", "owner", "created_at", "updated_at"}


def test_defaults_are_applied(client, auth):
    body = client.post("/tickets", json={"title": "Only a title"}, headers=auth("alice")).json()
    assert body["priority"] == "normal" and body["description"] == ""


@pytest.mark.parametrize("payload", [
    {},                                              # missing title
    {"title": ""},
    {"title": "   "},                                # whitespace only
    {"title": 123},                                  # wrong type
    {"title": None},
    {"title": ["a"]},
    {"title": "ok", "priority": "urgent"},           # not in the allowed list
    {"title": "ok", "description": 5},
    {"title": "ok", "unknown_field": "x"},           # unknown fields refused
    {"title": "bad\x00title"},                       # control characters
    {"title": "tab\there"},
])
def test_invalid_ticket_bodies_are_rejected(client, auth, payload):
    assert client.post("/tickets", json=payload, headers=auth("alice")).status_code == 422


def test_title_length_boundaries(client, auth):                                # edge cases
    assert client.post("/tickets", json={"title": "a" * 100}, headers=auth("alice")).status_code == 201
    assert client.post("/tickets", json={"title": "a" * 101}, headers=auth("alice")).status_code == 422
    assert client.post("/tickets", json={"title": "a"}, headers=auth("alice")).status_code == 201


def test_description_length_boundaries(client, auth):                          # edge cases
    assert client.post("/tickets", json={"title": "t", "description": "d" * 1000}, headers=auth("alice")).status_code == 201
    assert client.post("/tickets", json={"title": "t", "description": "d" * 1001}, headers=auth("alice")).status_code == 422


def test_whitespace_is_trimmed(client, auth):
    body = client.post("/tickets", json={"title": "  padded  "}, headers=auth("alice")).json()
    assert body["title"] == "padded"


def test_unicode_text_is_accepted(client, auth):                               # edge case
    title = "Café – 请求 – заявка"
    body = client.post("/tickets", json={"title": title}, headers=auth("alice")).json()
    assert body["title"] == title


def test_newlines_allowed_in_description_only(client, auth):
    assert client.post("/tickets", json={"title": "t", "description": "line1\nline2"}, headers=auth("alice")).status_code == 201
    assert client.post("/tickets", json={"title": "line1\nline2"}, headers=auth("alice")).status_code == 422


def test_script_like_text_is_stored_as_data_and_returned_as_json(client, auth):   # edge case
    payload = "<script>alert(1)</script>' OR '1'='1"
    created = client.post("/tickets", json={"title": payload}, headers=auth("alice"))
    assert created.status_code == 201
    fetched = client.get(f"/tickets/{created.json()['id']}", headers=auth("alice"))
    assert fetched.json()["title"] == payload                       # stored as plain data
    assert fetched.headers["content-type"].startswith("application/json")
    assert fetched.headers["x-content-type-options"] == "nosniff"   # browsers must not guess HTML


def test_wrong_content_type_is_415(client, auth):
    response = client.post("/tickets", content="title=x", headers={**auth("alice"),
                           "Content-Type": "application/x-www-form-urlencoded"})
    assert response.status_code == 415


def test_oversized_body_is_413(client, auth):
    response = client.post("/tickets", content=b'{"title":"x","description":"' + b"a" * 20000 + b'"}',
                           headers={**auth("alice"), **JSON})
    assert response.status_code == 413


def test_chunked_oversized_body_is_413(app, auth):
    async def chunks():
        yield b'{"title":"ticket","description":"'
        yield b"a" * 12000
        yield b'"}'

    async def send_request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as streamed:
            request = streamed.build_request("POST", "/tickets", content=chunks(),
                                             headers={**auth("alice"), **JSON})
            assert "content-length" not in request.headers
            return await streamed.send(request)

    response = asyncio.run(send_request())
    body = response.json()["error"]
    assert response.status_code == 413 and body["code"] == "payload_too_large"
    assert body["request_id"] == response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"


def test_chunked_body_within_limit_is_replayed(app, auth):
    async def chunks():
        yield b'{"title":"streamed","description":"'
        yield b'body"}'

    async def send_request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as streamed:
            request = streamed.build_request("POST", "/tickets", content=chunks(),
                                             headers={**auth("alice"), **JSON})
            assert "content-length" not in request.headers
            return await streamed.send(request)

    response = asyncio.run(send_request())
    assert response.status_code == 201
    assert response.json()["title"] == "streamed"


def test_invalid_json_is_422_and_not_echoed(client, auth):
    response = client.post("/tickets", content=b"{not json at all", headers={**auth("alice"), **JSON})
    assert response.status_code == 422 and "not json at all" not in response.text


def test_validation_errors_do_not_echo_submitted_values(client, auth):
    response = client.post("/tickets", json={"title": ["secret-value-123"]}, headers=auth("alice"))
    assert response.status_code == 422 and "secret-value-123" not in response.text
    assert response.json()["error"]["fields"][0]["field"] == "title"


@pytest.mark.parametrize("ticket_id", ["not-a-uuid", "1", "../../etc/passwd", "%00", "a" * 300])
def test_malformed_ticket_ids_are_404_not_500(client, auth, ticket_id):
    assert client.get(f"/tickets/{ticket_id}", headers=auth("alice")).status_code == 404


def test_well_formed_unknown_id_is_404(client, auth):
    assert client.get(f"/tickets/{uuid.uuid4()}", headers=auth("alice")).status_code == 404


# ---- pagination -------------------------------------------------------------------------------
def test_pagination_limit_and_offset(client, auth, make_ticket):
    for i in range(3):
        make_ticket("alice", title=f"t{i}")
    page = client.get("/tickets?limit=2", headers=auth("alice")).json()
    assert len(page["items"]) == 2 and page["total"] == 4          # 3 new + 1 seeded
    rest = client.get("/tickets?limit=2&offset=2", headers=auth("alice")).json()
    assert len(rest["items"]) == 2


@pytest.mark.parametrize("query", ["limit=0", "limit=51", "limit=-1", "limit=abc", "offset=-1", "offset=99999"])
def test_bad_pagination_values_are_rejected(client, auth, query):
    assert client.get(f"/tickets?{query}", headers=auth("alice")).status_code == 422


def test_maximum_page_size_is_accepted(client, auth):                          # edge case
    assert client.get("/tickets?limit=50", headers=auth("alice")).status_code == 200
