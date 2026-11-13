"""Support-ticket API: authentication, role checks, input validation, rate limiting, safe errors.
Local use only. All users and tickets are fictional."""
import logging
import time
import uuid

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings
from .deps import get_current_user, require_roles
from .errors import ApiError, error_response
from .models import LoginRequest, RoleUpdate, StatusUpdate, TicketCreate
from .ratelimit import SlidingWindowLimiter
from .security import DUMMY_HASH, create_token, verify_password
from .store import Store, User

log = logging.getLogger("secure-api")
DOC_PATHS = ("/docs", "/redoc", "/openapi.json")


def public_ticket(t: dict) -> dict:
    """Explicit allow-list of fields sent to clients."""
    return {k: t[k] for k in ("id", "title", "description", "priority", "status", "owner", "created_at", "updated_at")}


def can_view(user: User, ticket: dict) -> bool:
    return user.role in ("agent", "admin") or ticket["owner"] == user.username


def create_app(settings: Settings | None = None, clock=time.monotonic) -> FastAPI:
    settings = settings or Settings.from_env()
    docs = {} if settings.enable_docs else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title="Secure Local Ticket API", **docs)
    app.state.settings = settings
    app.state.store = Store()
    app.state.limiter = SlidingWindowLimiter(clock)

    # ------------------------------------------------------------------ guards
    def precheck(request: Request):
        """Runs before routing: rate limit, body size, content type."""
        client = request.client.host if request.client else "unknown"  # never trust X-Forwarded-For
        is_login = request.url.path == "/auth/login"
        limit = settings.login_limit if is_login else settings.default_limit
        allowed, retry_after = request.app.state.limiter.check(f"{client}|{'login' if is_login else 'all'}", limit)
        if not allowed:
            return error_response(request, 429, "rate_limited", "Too many requests. Try again later.",
                                  {"Retry-After": str(retry_after)})
        length = request.headers.get("content-length")
        if length is not None:
            if not length.isdigit():
                return error_response(request, 400, "bad_request", "Invalid Content-Length.")
            if int(length) > settings.max_body_bytes:
                return error_response(request, 413, "payload_too_large", "Request body too large.")
        has_body = (length not in (None, "0")) or "transfer-encoding" in request.headers
        if request.method in ("POST", "PUT", "PATCH") and has_body:
            if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
                return error_response(request, 415, "unsupported_media_type", "Content-Type must be application/json.")
        return None

    @app.middleware("http")
    async def guard(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex[:12]
        request.state.username = None
        started = time.monotonic()
        response = precheck(request)
        if response is None:
            try:
                response = await call_next(request)
            except Exception:
                log.exception("req=%s unhandled error", request.state.request_id)  # detail stays in the server log
                response = error_response(request, 500, "internal_error", "Something went wrong.")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Request-ID"] = request.state.request_id
        if not request.url.path.startswith(DOC_PATHS):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
            response.headers["X-Frame-Options"] = "DENY"
        # Safe log line: no tokens, passwords, query strings or bodies.
        log.info("req=%s method=%s path=%s status=%s user=%s ms=%d", request.state.request_id, request.method,
                 request.url.path, response.status_code, request.state.username or "-",
                 int((time.monotonic() - started) * 1000))
        return response

    # --------------------------------------------------------- error handlers
    @app.exception_handler(ApiError)
    async def on_api_error(request: Request, exc: ApiError):
        return error_response(request, exc.status, exc.code, exc.message, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def on_validation_error(request: Request, exc: RequestValidationError):
        # Report which field failed and why, but never echo the submitted value back.
        fields = [{"field": ".".join(str(p) for p in e["loc"] if p != "body") or "body", "message": e["msg"]}
                  for e in exc.errors()]
        return error_response(request, 422, "validation_error", "Request validation failed.", fields=fields)

    @app.exception_handler(StarletteHTTPException)
    async def on_http_error(request: Request, exc: StarletteHTTPException):
        generic = {404: ("not_found", "Resource not found."), 405: ("method_not_allowed", "Method not allowed.")}
        code, message = generic.get(exc.status_code, ("http_error", "Request could not be processed."))
        return error_response(request, exc.status_code, code, message, dict(exc.headers or {}))

    # ------------------------------------------------------------------ routes
    def find_ticket(ticket_id: str):
        try:
            return app.state.store.tickets.get(str(uuid.UUID(ticket_id)))
        except ValueError:
            return None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/auth/login")
    def login(payload: LoginRequest):
        user = app.state.store.users.get(payload.username)
        password_ok = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
        if user is None or user.disabled or not password_ok:
            raise ApiError(401, "invalid_credentials", "Invalid username or password.")
        return {"access_token": create_token(user.username, settings), "token_type": "bearer",
                "expires_in": settings.token_ttl_seconds}

    @app.get("/me")
    def me(user: User = Depends(get_current_user)):
        return {"username": user.username, "role": user.role}

    @app.post("/tickets", status_code=201)
    def create_ticket(payload: TicketCreate, user: User = Depends(get_current_user)):
        # The owner comes from the verified identity, never from the request body.
        ticket = app.state.store.add_ticket(user.username, payload.title, payload.description, payload.priority)
        return public_ticket(ticket)

    @app.get("/tickets")
    def list_tickets(limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0, le=10_000),
                     user: User = Depends(get_current_user)):
        tickets = sorted(app.state.store.tickets.values(), key=lambda t: (t["created_at"], t["id"]))
        visible = [t for t in tickets if can_view(user, t)]
        return {"items": [public_ticket(t) for t in visible[offset:offset + limit]],
                "total": len(visible), "limit": limit, "offset": offset}

    @app.get("/tickets/{ticket_id}")
    def get_ticket(ticket_id: str, user: User = Depends(get_current_user)):
        ticket = find_ticket(ticket_id)
        # Not found and not yours look identical, so ticket IDs cannot be enumerated.
        if ticket is None or not can_view(user, ticket):  # MUT:ticket-ownership
            raise ApiError(404, "not_found", "Resource not found.")
        return public_ticket(ticket)

    @app.patch("/tickets/{ticket_id}/status")
    def update_status(ticket_id: str, payload: StatusUpdate, user: User = Depends(require_roles("agent", "admin"))):
        ticket = find_ticket(ticket_id)
        if ticket is None:
            raise ApiError(404, "not_found", "Resource not found.")
        if ticket["status"] == "closed":
            raise ApiError(409, "conflict", "A closed ticket cannot be changed.")
        ticket["status"], ticket["updated_at"] = payload.status, int(time.time())
        return public_ticket(ticket)

    @app.delete("/tickets/{ticket_id}", status_code=204)
    def delete_ticket(ticket_id: str, user: User = Depends(require_roles("admin"))):  # MUT:rbac-delete
        ticket = find_ticket(ticket_id)
        if ticket is None:
            raise ApiError(404, "not_found", "Resource not found.")
        del app.state.store.tickets[ticket["id"]]
        return Response(status_code=204)

    @app.get("/admin/users")
    def list_users(user: User = Depends(require_roles("admin"))):  # MUT:rbac-admin-users
        return {"items": [{"username": u.username, "role": u.role, "disabled": u.disabled}
                          for u in app.state.store.users.values()]}  # password hashes are never returned

    @app.patch("/admin/users/{username}/role")
    def change_role(username: str, payload: RoleUpdate, admin: User = Depends(require_roles("admin"))):
        target = app.state.store.users.get(username)
        if target is None:
            raise ApiError(404, "not_found", "Resource not found.")
        if target.username == admin.username and payload.role != "admin":
            raise ApiError(409, "conflict", "You cannot remove your own admin role.")
        target.role = payload.role
        return {"username": target.username, "role": target.role}

    return app


app = create_app()
