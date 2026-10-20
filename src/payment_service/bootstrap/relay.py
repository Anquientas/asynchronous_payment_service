import asyncio
import logging

from faststream.rabbit import RabbitBroker

from payment_service.application.constants import ErrorMessage
from payment_service.application.use_cases.relay_outbox import RelayOutbox
from payment_service.config import get_settings
from payment_service.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)
from payment_service.infrastructure.database.unit_of_work import (
    SqlalchemyUnitOfWork,
)
from payment_service.infrastructure.messaging.constants import (
    PaymentsRoutingKey,
)
from payment_service.infrastructure.messaging.publisher import (
    RabbitMessagePublisher,
)
from payment_service.infrastructure.messaging.topology import declare_topology

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = create_database_engine(settings.postgres.url)
    session_factory = create_session_factory(engine)
    broker = RabbitBroker(settings.rabbitmq.url)

    try:
        async with broker:
            await declare_topology(broker)
            publisher = RabbitMessagePublisher(broker)
            while True:
                relay = RelayOutbox(
                    uow=SqlalchemyUnitOfWork(session_factory),
                    publisher=publisher,
                    batch_limit=settings.outbox_rabbitmq.batch_limit,
                    max_attempts=settings.outbox_rabbitmq.attempts_maximum,
                    routing_key=PaymentsRoutingKey.NEW,
                )
                try:
                    await relay()
                except Exception:
                    logger.exception(ErrorMessage.OUTBOX_RELAY_FAILED)
                await asyncio.sleep(
                    settings.outbox_rabbitmq.dispatch_interval_seconds
                )
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
