from collections.abc import Mapping

from app.services.webhooks.mock_hmac import MockHmacVerifier


class BrankasVerifier(MockHmacVerifier):
    """Sandbox-oriented verifier.

    Replace this with Brankas' production signature verification when wiring a
    real Brankas integration. Keeping a separate class avoids coupling provider
    semantics to mock_bank.
    """

    def verify(self, headers: Mapping[str, str], raw_body: bytes) -> bool:
        return super().verify(headers, raw_body)

