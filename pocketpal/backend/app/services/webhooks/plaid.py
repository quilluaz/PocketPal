from collections.abc import Mapping

from app.services.webhooks.base import WebhookVerifier


class PlaidVerifier(WebhookVerifier):
    """Structured placeholder for Plaid's JWT/JWK webhook verification.

    Plaid webhooks should be verified using Plaid's signed JWT/JWK flow. V1 keeps
    the provider boundary explicit and routes local acceptance tests through
    mock_bank instead of pretending Plaid uses the mock HMAC signature.
    """

    def verify(self, headers: Mapping[str, str], raw_body: bytes) -> bool:
        return False

