import asyncio
import random

from payment_service.domain.entities import Payment
from payment_service.infrastructure.gateway.constants import (
    DELAY_SECONDS_MAXIMUM,
    DELAY_SECONDS_MINIMUM,
    SUCCESS_RATE,
)


class EmulatedPaymentGateway:
    async def charge(self, payment: Payment) -> bool:
        await asyncio.sleep(
            random.uniform(
                DELAY_SECONDS_MINIMUM,
                DELAY_SECONDS_MAXIMUM,
            )
        )
        return random.random() < SUCCESS_RATE
