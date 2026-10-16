from payment_service.application.constants import ErrorMessage, EventType
from payment_service.application.dto import CreatePaymentInputDTO
from payment_service.application.exceptions import (
    DuplicateIdempotencyKeyError,
    IdempotencyConflictError,
)
from payment_service.application.interfaces import UnitOfWork
from payment_service.domain.entities import Payment


class CreatePayment:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def __call__(self, data: CreatePaymentInputDTO) -> Payment:
        async with self._uow:
            existing = await self._find_and_check_existing(data=data)
            if existing is not None:
                return existing
            payment = Payment.create(
                amount=data.amount,
                currency=data.currency,
                description=data.description,
                metadata=data.metadata,
                idempotency_key=data.idempotency_key,
                webhook_url=data.webhook_url,
            )
            await self._uow.payment_repository.add(payment=payment)
            await self._uow.outbox_repository.add(
                event_type=EventType.CREATED,
                payload={'payment_id': str(payment.id)},
            )
            try:
                await self._uow.commit()
                return payment
            except DuplicateIdempotencyKeyError:
                existing = await self._find_and_check_existing(data=data)
                if existing is None:
                    raise
                return existing

    async def _find_and_check_existing(
        self,
        data: CreatePaymentInputDTO,
    ) -> Payment | None:
        existing = await self._uow.payment_repository.get_by_idempotency_key(
            idempotency_key=data.idempotency_key,
        )
        if existing is not None:
            self._verify_data_equality(
                existing=existing,
                data=data,
            )
        return existing

    def _verify_data_equality(
        self,
        existing: Payment,
        data: CreatePaymentInputDTO,
    ) -> None:
        for parameter in (
            'amount',
            'currency',
            'description',
            'metadata',
            'webhook_url',
        ):
            if getattr(existing, parameter) != getattr(data, parameter):
                raise IdempotencyConflictError(
                    ErrorMessage.INCORRECT_PAYMENT_PARAMETER.format(
                        idempotency_key=data.idempotency_key,
                        parameter=parameter,
                    )
                )
