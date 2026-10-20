import asyncio
from typing import Any

import httpx

from payment_service.infrastructure.webhook.constants import (
    WEBHOOK_ATTEMPTS,
    WEBHOOK_BASE_DELAY_SECONDS,
)


class HttpxWebhookSender:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def send(self, url: str, payload: dict[str, Any]) -> None:
        for attempt in range(WEBHOOK_ATTEMPTS):
            try:
                response = await self._client.post(
                    url=url,
                    json=payload,
                )
                response.raise_for_status()
                return
            except httpx.HTTPError:
                if attempt == WEBHOOK_ATTEMPTS - 1:
                    raise
                await asyncio.sleep(WEBHOOK_BASE_DELAY_SECONDS * 2**attempt)
