"""Application settings. No real secrets are stored here or in git.

MOCKMATE_SECRET_KEY must be set in production. In local dev, if it is
missing, an ephemeral key is generated (encrypted provider keys will not
survive a restart) and a warning is logged.
"""
from __future__ import annotations

import hashlib
import base64
import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)


class Settings:
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./mockmate.db")
    cors_origins: list[str] = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]
    session_cookie_name: str = "mockmate_session"
    session_max_age_seconds: int = 7 * 24 * 3600

    def __init__(self) -> None:
        raw = os.environ.get("MOCKMATE_SECRET_KEY")
        if not raw:
            raw = secrets.token_hex(32)
            logger.warning(
                "MOCKMATE_SECRET_KEY is not set; using an ephemeral key. "
                "Encrypted provider credentials will not survive a restart. "
                "Set MOCKMATE_SECRET_KEY in production."
            )
        self.secret_key = raw
        self.fernet_key = _fernet_key(raw)


settings = Settings()
