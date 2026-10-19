from http import HTTPStatus

from payment_service.application.exceptions import (
    IdempotencyConflictError,
    PaymentNotFoundError,
)
from payment_service.domain.exceptions import InvalidAmountError

EXCEPTION_STATUS_CODES = {
    PaymentNotFoundError: HTTPStatus.NOT_FOUND,
    IdempotencyConflictError: HTTPStatus.CONFLICT,
    InvalidAmountError: HTTPStatus.UNPROCESSABLE_ENTITY,
}
