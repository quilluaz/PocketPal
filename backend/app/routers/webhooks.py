from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.config import Settings, get_settings
from app.db import database
from app.models.webhook import MockBankWebhookPayload
from app.services.webhooks.brankas import BrankasVerifier
from app.services.webhooks.mock_hmac import MockHmacVerifier
from app.services.webhooks.plaid import PlaidVerifier
from app.services.webhooks.processor import WebhookProcessor

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verifier_for(provider: str, settings: Settings):
    if provider == "mock_bank":
        return MockHmacVerifier(settings.mock_webhook_secret)
    if provider == "plaid":
        return PlaidVerifier()
    if provider == "brankas":
        return BrankasVerifier(settings.mock_webhook_secret)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "provider_not_supported", "message": f"Provider {provider} is not supported."},
    )


async def process_mock_bank_payload(payload: MockBankWebhookPayload) -> None:
    await WebhookProcessor(database).process_mock_bank(payload)


@router.post("/bank/{provider}")
async def bank_webhook(
    provider: str,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
):
    raw_body = await request.body()
    verifier = verifier_for(provider, settings)
    if not verifier.verify(request.headers, raw_body):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_signature", "message": "Webhook signature verification failed."},
        )

    if provider != "mock_bank":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "code": "provider_verification_not_implemented",
                "message": "Only mock_bank processing is implemented in V1.",
            },
        )

    payload = MockBankWebhookPayload.model_validate_json(raw_body)
    background_tasks.add_task(process_mock_bank_payload, payload)
    return {"status": "accepted"}

