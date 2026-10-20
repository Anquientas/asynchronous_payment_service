from faststream.rabbit import (
    ExchangeType,
    RabbitBroker,
    RabbitExchange,
    RabbitQueue,
)

from payment_service.infrastructure.messaging.constants import (
    ExchangeName,
    PaymentsRoutingKey,
    QueueName,
)

PAYMENTS_EXCHANGE = RabbitExchange(
    name=ExchangeName.PAYMENTS,
    type=ExchangeType.DIRECT,
    durable=True,
)

DLX_EXCHANGE = RabbitExchange(
    name=ExchangeName.DLX,
    type=ExchangeType.DIRECT,
    durable=True,
)

PAYMENTS_QUEUE = RabbitQueue(
    name=QueueName.PAYMENTS,
    durable=True,
    routing_key=PaymentsRoutingKey.NEW,
    arguments={'x-dead-letter-exchange': ExchangeName.DLX},
)

DLQ = RabbitQueue(
    name=QueueName.DLQ,
    durable=True,
    routing_key=PaymentsRoutingKey.NEW,
)


async def declare_topology(broker: RabbitBroker) -> None:
    payments_exchange = await broker.declare_exchange(PAYMENTS_EXCHANGE)
    dlx_exchange = await broker.declare_exchange(DLX_EXCHANGE)
    payments_queue = await broker.declare_queue(PAYMENTS_QUEUE)
    dlq = await broker.declare_queue(DLQ)
    await payments_queue.bind(
        payments_exchange,
        routing_key=PaymentsRoutingKey.NEW,
    )
    await dlq.bind(
        dlx_exchange,
        routing_key=PaymentsRoutingKey.NEW,
    )
