from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from payment_service.application.constants import EventType
from payment_service.application.dto import OutboxMessage
from payment_service.domain.constants import Currency, PaymentStatus
from payment_service.domain.entities import Payment
from payment_service.infrastructure.database.models import (
    OutboxRabbitMQModel,
    PaymentModel,
)


def _get_current_time() -> datetime:
    return datetime.now(UTC)


def _to_model(payment: Payment) -> PaymentModel:
    return PaymentModel(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata_=payment.metadata,
        status=payment.status,
        webhook_url=payment.webhook_url,
        idempotency_key=payment.idempotency_key,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )


def _to_entity(model: PaymentModel) -> Payment:
    return Payment(
        id=model.id,
        amount=model.amount,
        currency=Currency(model.currency),
        description=model.description,
        metadata=model.metadata_,
        status=PaymentStatus(model.status),
        webhook_url=model.webhook_url,
        idempotency_key=model.idempotency_key,
        created_at=model.created_at,
        processed_at=model.processed_at,
    )


def _to_outbox_message(model: OutboxRabbitMQModel) -> OutboxMessage:
    return OutboxMessage(
        message_id=model.id,
        event_type=model.event_type,
        payload=model.payload,
        attempts=model.attempts,
    )


class SqlalchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, payment: Payment) -> None:
        model = _to_model(payment=payment)
        self._session.add(model)

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        result = await self._session.scalar(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        if result is None:
            return None
        return _to_entity(model=result)

    async def get_by_id_for_update(self, payment_id: UUID) -> Payment | None:
        result = await self._session.scalar(
            select(PaymentModel)
            .where(PaymentModel.id == payment_id)
            .with_for_update()
        )
        if result is None:
            return None
        return _to_entity(model=result)

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Payment | None:
        result = await self._session.scalar(
            select(PaymentModel).where(
                PaymentModel.idempotency_key == idempotency_key
            )
        )
        if result is None:
            return None
        return _to_entity(model=result)

    async def update(self, payment: Payment) -> None:
        await self._session.execute(
            update(PaymentModel)
            .where(PaymentModel.id == payment.id)
            .values(status=payment.status, processed_at=payment.processed_at)
        )


class SqlalchemyOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        event_type: EventType,
        payload: dict[str, Any],
    ) -> None:
        outbox_rabbitmq = OutboxRabbitMQModel(
            event_type=event_type,
            payload=payload,
        )
        self._session.add(outbox_rabbitmq)

    async def get_unpublished(
        self,
        limit: int,
        max_attempts: int,
    ) -> list[OutboxMessage]:
        results = await self._session.scalars(
            select(OutboxRabbitMQModel)
            .where(
                OutboxRabbitMQModel.published_at.is_(None),
                OutboxRabbitMQModel.attempts < max_attempts,
            )
            .order_by(OutboxRabbitMQModel.created_at)
            .with_for_update(skip_locked=True)
            .limit(limit=limit)
        )
        models = results.all()
        return [_to_outbox_message(model) for model in models]

    async def mark_published(self, message_id: UUID) -> None:
        await self._session.execute(
            update(OutboxRabbitMQModel)
            .where(OutboxRabbitMQModel.id == message_id)
            .values(published_at=_get_current_time())
        )

    async def increment_attempts(self, message_id: UUID) -> None:
        await self._session.execute(
            update(OutboxRabbitMQModel)
            .where(OutboxRabbitMQModel.id == message_id)
            .values(attempts=OutboxRabbitMQModel.attempts + 1)
        )
