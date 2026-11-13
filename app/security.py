"""Password hashing (scrypt, standard library) and signed access tokens (JWT, HS256)."""
import hashlib
import hmac
import os
import time

import jwt

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Return 'scrypt$N$r$p$salt$hash'. A fresh random salt makes equal passwords hash differently."""
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, n, r, p, salt_hex, hash_hex = stored.split("$")
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex),
                                n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except ValueError:
        return False
    return hmac.compare_digest(actual, expected)  # constant-time comparison


# Used for unknown usernames so a login attempt costs the same time either way.
DUMMY_HASH = hash_password("not-a-real-password")


def create_token(username: str, settings, ttl_seconds: int | None = None, now: int | None = None) -> str:
    """The token carries identity only (sub). The role is looked up on every request."""
    issued = int(time.time() if now is None else now)
    ttl = settings.token_ttl_seconds if ttl_seconds is None else ttl_seconds
    claims = {"sub": username, "iat": issued, "exp": issued + ttl, "iss": settings.issuer}
    return jwt.encode(claims, settings.secret_key, algorithm="HS256")


def decode_token(token: str, settings) -> dict:
    """Verify signature, expiry and issuer. The algorithm is pinned, so 'alg: none' is refused."""
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=["HS256"],
        issuer=settings.issuer,
        options={"require": ["exp", "iat", "sub", "iss"]},
    )
