import base64
import binascii
import hashlib
import hmac
import json
import time

from app.config import Settings


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def credentials_are_valid(self, username: str, password: str) -> bool:
        expected_username = self.settings.commercial_username.encode()
        expected_password = self.settings.commercial_password.encode()
        username_is_valid = hmac.compare_digest(
            username.strip().lower().encode(), expected_username
        )
        password_is_valid = hmac.compare_digest(password.encode(), expected_password)
        return username_is_valid and password_is_valid

    def create_session(self, username: str) -> str:
        payload = {"sub": username, "exp": int(time.time()) + self.settings.session_ttl_seconds}
        encoded = self._encode(json.dumps(payload, separators=(",", ":")).encode())
        signature = self._sign(encoded)
        return f"{encoded}.{signature}"

    def verify_session(self, token: str | None) -> str | None:
        if not token:
            return None
        try:
            encoded, signature = token.split(".", maxsplit=1)
            if not hmac.compare_digest(signature, self._sign(encoded)):
                return None
            payload = json.loads(self._decode(encoded))
            if payload.get("exp", 0) < int(time.time()):
                return None
            username = payload.get("sub")
            return username if isinstance(username, str) else None
        except (ValueError, TypeError, binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _sign(self, value: str) -> str:
        digest = hmac.new(
            self.settings.session_secret.encode(), value.encode(), hashlib.sha256
        ).digest()
        return self._encode(digest)

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode()

    @staticmethod
    def _decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)
