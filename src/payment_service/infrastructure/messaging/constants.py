from enum import StrEnum


class PaymentsRoutingKey(StrEnum):
    NEW = 'payments.new'


class ExchangeName(StrEnum):
    DLX = 'payments.dlx'
    PAYMENTS = 'payments'


class QueueName(StrEnum):
    PAYMENTS = 'payments.new'
    DLQ = 'payments.new.dlq'
