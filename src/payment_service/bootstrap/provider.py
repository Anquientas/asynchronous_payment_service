from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from payment_service.application.interfaces import (
    PaymentGateway,
    WebhookSender,
)
from payment_service.application.use_cases.create_payment import CreatePayment
from payment_service.application.use_cases.get_payment import GetPayment
from payment_service.application.use_cases.process_payment import (
    ProcessPayment,
)
from payment_service.infrastructure.database.unit_of_work import (
    SqlalchemyUnitOfWork,
)


class SqlalchemyUseCaseProvider:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self._session_factory = session_factory

    def create_payment(self) -> CreatePayment:
        return CreatePayment(SqlalchemyUnitOfWork(self._session_factory))

    def get_payment(self) -> GetPayment:
        return GetPayment(SqlalchemyUnitOfWork(self._session_factory))


class SqlalchemyConsumerProvider:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        gateway: PaymentGateway,
        webhook_sender: WebhookSender,
    ) -> None:
        self._session_factory = session_factory
        self._gateway = gateway
        self._webhook_sender = webhook_sender

    def process_payment(self) -> ProcessPayment:
        return ProcessPayment(
            uow=SqlalchemyUnitOfWork(self._session_factory),
            gateway=self._gateway,
            webhook_sender=self._webhook_sender,
        )
