import asyncio

import httpx
from faststream.rabbit import RabbitBroker

from payment_service.bootstrap.provider import SqlalchemyConsumerProvider
from payment_service.config import get_settings
from payment_service.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)
from payment_service.infrastructure.gateway.emulated_gateway import (
    EmulatedPaymentGateway,
)
from payment_service.infrastructure.messaging.topology import (
    PAYMENTS_EXCHANGE,
    PAYMENTS_QUEUE,
    declare_topology,
)
from payment_service.infrastructure.webhook.constants import (
    WEBHOOK_TIMEOUT_SECONDS,
)
from payment_service.infrastructure.webhook.httpx_sender import (
    HttpxWebhookSender,
)
from payment_service.presentation.consumer.handlers import create_router


async def main() -> None:
    settings = get_settings()
    engine = create_database_engine(settings.postgres.url)
    client = httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS)
    provider = SqlalchemyConsumerProvider(
        session_factory=create_session_factory(engine=engine),
        gateway=EmulatedPaymentGateway(),
        webhook_sender=HttpxWebhookSender(client=client),
    )
    broker = RabbitBroker(settings.rabbitmq.url)
    broker.include_router(
        create_router(provider, PAYMENTS_QUEUE, PAYMENTS_EXCHANGE)
    )

    try:
        async with broker:
            await declare_topology(broker)
            await broker.start()
            await asyncio.Event().wait()
    finally:
        await client.aclose()
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
