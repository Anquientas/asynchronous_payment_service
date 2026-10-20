import logging

from payment_service.application.constants import ErrorMessage
from payment_service.application.interfaces import (
    MessagePublisher,
    UnitOfWork,
)


class RelayOutbox:
    def __init__(
        self,
        uow: UnitOfWork,
        publisher: MessagePublisher,
        batch_limit: int,
        max_attempts: int,
        routing_key: str,
    ) -> None:
        self._uow = uow
        self._publisher = publisher
        self._batch_limit = batch_limit
        self._max_attempts = max_attempts
        self._routing_key = routing_key

    async def __call__(self) -> None:
        async with self._uow:
            messages = await self._uow.outbox_repository.get_unpublished(
                limit=self._batch_limit,
                max_attempts=self._max_attempts,
            )
            for message in messages:
                try:
                    await self._publisher.publish(
                        routing_key=self._routing_key,
                        payload=message.payload,
                        message_id=str(message.message_id),
                    )
                except Exception:
                    await self._uow.outbox_repository.increment_attempts(
                        message_id=message.message_id,
                    )
                    logger.exception(
                        ErrorMessage.OUTBOX_FAILED_PUBLISH,
                        message.message_id,
                    )
                    continue
                await self._uow.outbox_repository.mark_published(
                    message_id=message.message_id,
                )
            await self._uow.commit()


logger = logging.getLogger(__name__)
