class ApplicationError(Exception):
    pass


class PaymentNotFoundError(ApplicationError):
    pass


class IdempotencyConflictError(ApplicationError):
    pass
