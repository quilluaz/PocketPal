from abc import ABC, abstractmethod
from collections.abc import Mapping


class WebhookVerifier(ABC):
    @abstractmethod
    def verify(self, headers: Mapping[str, str], raw_body: bytes) -> bool:
        """Return true when the provider signature is trusted."""


def lower_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}

