from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: UUID


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_dev_user_id: str | None = Header(default=None, alias="X-Dev-User-Id"),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if settings.app_env == "development" and x_dev_user_id:
        return CurrentUser(user_id=UUID(x_dev_user_id))

    if credentials is None:
        if settings.app_env == "development":
            return CurrentUser(user_id=settings.development_user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "missing_authorization", "message": "Bearer token is required."},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Supabase JWT validation failed."},
        ) from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "missing_subject", "message": "Token does not contain a subject."},
        )
    return CurrentUser(user_id=UUID(subject))

