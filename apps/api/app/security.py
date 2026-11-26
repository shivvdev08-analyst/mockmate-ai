"""PIN hashing, Fernet encryption of provider keys, signed session cookies.

No API key or PIN is ever logged. Session tokens are HMAC-signed
(user_id + expiry) with the server secret; they are not JWTs and carry
no sensitive data.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from cryptography.fernet import Fernet, InvalidToken

from .config import settings

_PBKDF2_ITERATIONS = 200_000


def hash_pin(pin: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, _PBKDF2_ITERATIONS)
    return digest.hex(), salt.hex()


def verify_pin(pin: str, pin_hash: str, salt_hex: str) -> bool:
    candidate, _ = hash_pin(pin, salt_hex)
    return hmac.compare_digest(candidate, pin_hash)


def encrypt_secret(plaintext: str) -> str:
    return Fernet(settings.fernet_key).encrypt(plaintext.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return Fernet(settings.fernet_key).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("stored credential could not be decrypted") from exc


def mask_key(api_key: str) -> str:
    """gsk_abc...xyz -> gsk_••••wxyz ; short keys -> •••• + last 4."""
    if len(api_key) <= 8:
        return "••••" + api_key[-4:] if len(api_key) >= 4 else "••••"
    prefix = api_key[:4]
    return f"{prefix}••••{api_key[-4:]}"


def sign_session(user_id: int) -> str:
    expiry = int(time.time()) + settings.session_max_age_seconds
    payload = f"{user_id}:{expiry}"
    sig = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_session(token: str) -> int | None:
    try:
        user_id_s, expiry_s, sig = token.split(":")
        payload = f"{user_id_s}:{expiry_s}"
        expected = hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        if int(expiry_s) < int(time.time()):
            return None
        return int(user_id_s)
    except (ValueError, TypeError):
        return None
