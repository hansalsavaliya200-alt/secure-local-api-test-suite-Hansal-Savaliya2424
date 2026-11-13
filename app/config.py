"""Settings. Secrets come from the environment, never from source code."""
import logging
import os
import secrets
from dataclasses import dataclass

log = logging.getLogger("secure-api")


@dataclass
class Settings:
    secret_key: str
    issuer: str = "secure-local-api"
    token_ttl_seconds: int = 15 * 60
    max_body_bytes: int = 10 * 1024
    # (max requests, window in seconds) per client address
    login_limit: tuple = (5, 60)  # MUT:login-limit
    default_limit: tuple = (60, 60)
    enable_docs: bool = False  # interactive docs are OFF unless you ask for them

    @classmethod
    def from_env(cls) -> "Settings":
        key = os.environ.get("APP_SECRET_KEY")
        if key is None:
            key = secrets.token_urlsafe(32)
            log.warning("APP_SECRET_KEY not set: using a random key. Tokens stop working on restart.")
        elif len(key) < 32:
            raise ValueError("APP_SECRET_KEY must be at least 32 characters")
        return cls(secret_key=key, enable_docs=os.environ.get("APP_ENABLE_DOCS") == "1")
