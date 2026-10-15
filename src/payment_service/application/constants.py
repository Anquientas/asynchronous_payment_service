from enum import StrEnum


class EventType(StrEnum):
    CREATED = 'payment.created'


class ErrorMessage(StrEnum):
    PAYMENT_BY_ID_NOT_FOUND = (
        'Платеж с идентификатором {payment_id} не найден!'
    )
    INCORRECT_PAYMENT_PARAMETER = (
        'Платеж с идемпотентным ключом {idempotency_key} '
        'уже выполнен с другим значением параметра {parameter}!'
    )
