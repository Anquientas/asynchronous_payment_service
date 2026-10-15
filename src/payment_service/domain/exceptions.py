class DomainError(Exception):
    pass


class InvalidAmountError(DomainError):
    pass


class InvalidStatusTransitionError(DomainError):
    pass
