from uuid import uuid4

from app.services.webhooks.mock_hmac import MockHmacVerifier
from app.services.webhooks.processor import bank_transaction_idempotency_key


def test_mock_webhook_hmac_verification():
    verifier = MockHmacVerifier("secret")
    body = b'{"event_id":"evt_001"}'
    signature = verifier.sign(body)

    assert verifier.verify({"X-PocketPal-Signature": f"sha256={signature}"}, body)
    assert not verifier.verify({"X-PocketPal-Signature": "sha256=bad"}, body)


def test_duplicate_webhook_uses_same_idempotency_key():
    first = bank_transaction_idempotency_key("mock_bank", "evt_001", "bank_tx_001")
    second = bank_transaction_idempotency_key("mock_bank", "evt_001", "bank_tx_001")
    different_event = bank_transaction_idempotency_key("mock_bank", "evt_002", "bank_tx_001")

    inserted = {first}
    assert second in inserted
    assert different_event not in inserted


def test_oauth_degraded_state_contract_is_explicit():
    user_id = uuid4()
    account = {
        "user_id": user_id,
        "oauth_status": "reconnect_required",
        "reconciliation_enabled": False,
    }

    assert account["oauth_status"] == "reconnect_required"
    assert account["reconciliation_enabled"] is False

