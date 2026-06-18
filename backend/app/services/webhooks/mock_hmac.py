import hashlib
import hmac
from collections.abc import Mapping

from app.services.webhooks.base import WebhookVerifier, lower_headers


class MockHmacVerifier(WebhookVerifier):
    def __init__(self, secret: str) -> None:
        self.secret = secret

    def sign(self, raw_body: bytes) -> str:
        return hmac.new(self.secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    def verify(self, headers: Mapping[str, str], raw_body: bytes) -> bool:
        normalized = lower_headers(headers)
        supplied = (
            normalized.get("x-pocketpal-signature")
            or normalized.get("x-mock-bank-signature")
            or normalized.get("x-webhook-signature")
        )
        if supplied is None:
            return False
        if supplied.startswith("sha256="):
            supplied = supplied.removeprefix("sha256=")
        return hmac.compare_digest(self.sign(raw_body), supplied)

