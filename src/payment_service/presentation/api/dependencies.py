import secrets

from fastapi import Depends, Header, HTTPException, Request

from payment_service.config import Settings, get_settings
from payment_service.presentation.api.interfaces import UseCaseProvider


def get_provider(request: Request) -> UseCaseProvider:
    return request.app.state.provider


def verify_api_key(
    settings: Settings = Depends(get_settings),
    x_api_key: str | None = Header(default=None),
) -> None:
    if x_api_key is None:
        raise HTTPException(status_code=401)
    if not secrets.compare_digest(
        x_api_key.encode(),
        settings.api_key.get_secret_value().encode(),
    ):
        raise HTTPException(status_code=401)
