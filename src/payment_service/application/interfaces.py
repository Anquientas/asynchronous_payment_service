from typing import Any, Protocol, Self
from uuid import UUID

from payment_service.application.dto import OutboxMessage
from payment_service.domain.entities import Payment


class PaymentRepository(Protocol):
    async def add(self, payment: Payment) -> None: ...

    async def get_by_id(self, payment_id: UUID) -> Payment | None: ...

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Payment | None: ...


class OutboxRepository(Protocol):
    async def add(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None: ...

    async def get_unpublished(
        self,
        limit: int,
        max_attempts: int,
    ) -> list[OutboxMessage]: ...

    async def mark_published(self, message_id: UUID) -> None: ...

    async def increment_attempts(self, message_id: UUID) -> None: ...


class UnitOfWork(Protocol):
    payment_repository: PaymentRepository
    outbox_repository: OutboxRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class MessagePublisher(Protocol):
    async def publish(
        self,
        routing_key: str,
        payload: dict[str, Any],
        message_id: str,
    ) -> None: ...
