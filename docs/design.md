# Design notes

## Request pipeline

1. **Request guards:** apply the client-address rate limit, validate `Content-Length` (`400` for malformed values and `413` when over the limit), and require JSON for request bodies (`415`). A bounded ASGI reader enforces the 10 KiB limit for streamed bodies and bodies whose declared length is inaccurate.
2. **Authentication** (`get_current_user`): parse `Authorization: Bearer`, verify the JWT, load the user from the store. Any failure is the same `401` with `WWW-Authenticate: Bearer`.
3. **Role check** (`require_roles`): `403` if the user's *current* role is not allowed.
4. **Validation**: strict Pydantic models. Unknown fields are rejected, which blocks mass assignment (for example sending `owner`).
5. **Object-level check**: a user may touch only their own tickets; agents and admins may touch all.
6. **Response**: one error format, security headers, request ID, safe log line.

## Decisions and reasons

| Decision | Reason |
|---|---|
| Token carries identity only; the role comes from the store on every request | Role changes take effect on the next request, including requests using an existing token. Test: `test_role_is_read_from_the_server_not_the_token` |
| A foreign ticket returns 404, not 403 | The response does not confirm whether the ticket exists. Test: `test_foreign_ticket_and_missing_ticket_look_identical` |
| Algorithm pinned to HS256 and `exp/iat/sub/iss` required | Blocks `alg: none` and tokens that never expire (RFC 8725) |
| scrypt with random salt; dummy hash for unknown users; `hmac.compare_digest` | Increases password-guessing cost and reduces timing differences between unknown users and incorrect passwords |
| Limiter keys on the socket address, not `X-Forwarded-For` | Forwarding headers are client-controlled; the local Uvicorn launch disables proxy-header rewriting |
| Injectable clock in the limiter | Tests verify time-window behavior without sleeping |
| Admin cannot demote themselves (`409`) | Prevents an administrator from removing their own administrative access |
| Validation errors list field names and messages, never submitted values | Avoids echoing attacker input or secrets back |
| 500 returns a generic message; details only in server logs | Avoids leaking internals |
| Docs (`/docs`) off by default | Smaller attack surface; can be enabled for local exploration |

## Known limitations

The service uses in-memory state and a process-local rate limiter, runs over HTTP, and has no token revocation flow. See the report for the full limitations and recommendations.
