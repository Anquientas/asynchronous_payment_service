from uuid import UUID

from payment_service.application.constants import ErrorMessage
from payment_service.application.exceptions import PaymentNotFoundError
from payment_service.application.interfaces import UnitOfWork
from payment_service.domain.entities import Payment


class GetPayment:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def __call__(self, payment_id: UUID) -> Payment:
        async with self._uow:
            existing = await self._uow.payment_repository.get_by_id(
                payment_id=payment_id
            )
            if existing is None:
                raise PaymentNotFoundError(
                    ErrorMessage.PAYMENT_BY_ID_NOT_FOUND.format(
                        payment_id=payment_id
                    )
                )
            return existing
