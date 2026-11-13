# Design notes

## Request pipeline

1. **Pre-check middleware** (before routing): rate limit by client address, then validate `Content-Length` (400/413), then `Content-Type` for bodies (415). A bounded ASGI body reader also enforces the 10 KiB limit when a request is streamed or its declared length is inaccurate.
2. **Authentication** (`get_current_user`): parse `Authorization: Bearer`, verify the JWT, load the user from the store. Any failure is the same `401` with `WWW-Authenticate: Bearer`.
3. **Role check** (`require_roles`): `403` if the user's *current* role is not allowed.
4. **Validation**: strict Pydantic models. Unknown fields are rejected, which blocks mass assignment (for example sending `owner`).
5. **Object-level check**: a user may touch only their own tickets; agents and admins may touch all.
6. **Response**: one error format, security headers, request ID, safe log line.

## Decisions and reasons

| Decision | Reason |
|---|---|
| Token carries identity only; the role comes from the store each request | A demoted user loses power immediately; a stolen or old token cannot keep a stale role. Test: `test_role_is_read_from_the_server_not_the_token` |
| Foreign ticket returns 404, not 403 | 403 would confirm the ticket exists (enumeration). Test: `test_foreign_ticket_and_missing_ticket_look_identical` |
| Algorithm pinned to HS256 and `exp/iat/sub/iss` required | Blocks `alg: none` and tokens that never expire (RFC 8725) |
| scrypt with random salt; dummy hash for unknown users; `hmac.compare_digest` | Slows offline guessing; unknown users and wrong passwords take similar time and give the same answer |
| Limiter keys on the socket address, never `X-Forwarded-For` | The client controls that header. Lesson from Task 1, and found again at the uvicorn layer in this task |
| Injectable clock in the limiter | Tests can move time forward instantly instead of sleeping |
| Admin cannot demote themselves (409) | Prevents locking everyone out of admin functions |
| Validation errors list field names and messages, never submitted values | Avoids echoing attacker input or secrets back |
| 500 returns a generic message; details only in server logs | Avoids leaking internals |
| Docs (`/docs`) off by default | Smaller attack surface; can be enabled for local exploration |

## Known limitations

See the report. Main ones: in-memory state, single process, HTTP only, no token revocation.
