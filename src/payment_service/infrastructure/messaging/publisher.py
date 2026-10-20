from typing import Any

from faststream.rabbit import RabbitBroker

from payment_service.infrastructure.messaging.topology import (
    PAYMENTS_EXCHANGE,
)


class RabbitMessagePublisher:
    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    async def publish(
        self,
        payload: dict[str, Any],
        routing_key: str,
        message_id: str,
    ) -> None:
        await self._broker.publish(
            payload,
            exchange=PAYMENTS_EXCHANGE,
            routing_key=routing_key,
            message_id=message_id,
            persist=True,
        )
