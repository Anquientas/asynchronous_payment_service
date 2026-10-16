from typing import Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from payment_service.application.exceptions import (
    DuplicateIdempotencyKeyError,
)
from payment_service.infrastructure.database.repositories import (
    SqlalchemyOutboxRepository,
    SqlalchemyPaymentRepository,
)


class SqlalchemyUnitOfWork:
    payment_repository: SqlalchemyPaymentRepository
    outbox_repository: SqlalchemyOutboxRepository

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory
        self._session = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.payment_repository = SqlalchemyPaymentRepository(
            session=self._session
        )
        self.outbox_repository = SqlalchemyOutboxRepository(
            session=self._session
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as exception:
            await self.rollback()
            raise DuplicateIdempotencyKeyError() from exception

    async def rollback(self) -> None:
        await self._session.rollback()
