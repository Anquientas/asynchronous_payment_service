from enum import StrEnum


class Currency(StrEnum):
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'


class PaymentStatus(StrEnum):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class ErrorMessage(StrEnum):
    INCORRECT_AMOUNT = 'Полученная сумма {amount} меньше, либо равна 0!'
    INCORRECT_CHANGE_STATUS = (
        'Недопустимая попытка смены статуса платежа {status}!'
    )
