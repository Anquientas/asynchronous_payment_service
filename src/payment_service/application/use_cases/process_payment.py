from uuid import UUID

from payment_service.application.constants import ErrorMessage
from payment_service.application.exceptions import PaymentNotFoundError
from payment_service.application.interfaces import (
    PaymentGateway,
    UnitOfWork,
    WebhookSender,
)
from payment_service.domain.constants import PaymentStatus


class ProcessPayment:
    def __init__(
        self,
        uow: UnitOfWork,
        gateway: PaymentGateway,
        webhook_sender: WebhookSender,
    ) -> None:
        self._uow = uow
        self._gateway = gateway
        self._webhook_sender = webhook_sender

    async def __call__(self, payment_id: UUID) -> None:
        async with self._uow:
            payment = await self._uow.payment_repository.get_by_id_for_update(
                payment_id=payment_id
            )
            if payment is None:
                raise PaymentNotFoundError(
                    ErrorMessage.PAYMENT_BY_ID_NOT_FOUND.format(
                        payment_id=payment_id
                    )
                )
            if payment.status == PaymentStatus.PENDING:
                is_charged = await self._gateway.charge(payment)
                if is_charged:
                    payment.mark_succeeded()
                else:
                    payment.mark_failed()
                await self._uow.payment_repository.update(payment=payment)
                await self._uow.commit()
        await self._webhook_sender.send(
            payment.webhook_url,
            {
                'payment_id': str(payment.id),
                'status': payment.status,
                'amount': str(payment.amount),
                'currency': payment.currency,
                'processed_at': payment.processed_at.isoformat(),
            },
        )
