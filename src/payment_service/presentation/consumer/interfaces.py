from typing import Protocol

from payment_service.application.use_cases.process_payment import (
    ProcessPayment,
)


class ConsumerUseCaseProvider(Protocol):
    def process_payment(self) -> ProcessPayment: ...
