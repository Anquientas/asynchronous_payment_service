from faststream import AckPolicy
from faststream.rabbit import RabbitExchange, RabbitQueue, RabbitRouter

from payment_service.presentation.consumer.interfaces import (
    ConsumerUseCaseProvider,
)
from payment_service.presentation.consumer.schemas import (
    PaymentCreatedMessage,
)


def create_router(
    provider: ConsumerUseCaseProvider,
    queue: RabbitQueue,
    exchange: RabbitExchange,
) -> RabbitRouter:
    router = RabbitRouter()

    @router.subscriber(
        queue=queue,
        exchange=exchange,
        ack_policy=AckPolicy.REJECT_ON_ERROR,
    )
    async def handle_payment_created(body: PaymentCreatedMessage) -> None:
        use_case = provider.process_payment()
        await use_case(payment_id=body.payment_id)

    return router
