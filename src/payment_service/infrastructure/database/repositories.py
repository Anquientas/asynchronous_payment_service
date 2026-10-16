from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment_service.application.constants import EventType
from payment_service.domain.constants import Currency, PaymentStatus
from payment_service.domain.entities import Payment
from payment_service.infrastructure.database.models import (
    OutboxRabbitMQModel,
    PaymentModel,
)


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

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> Payment | None:
        result = await self._session.scalar(
            select(PaymentModel).where(
                PaymentModel.idempotency_key == idempotency_key
            )
        )
        if result is None:
            return None
        return _to_entity(model=result)


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
