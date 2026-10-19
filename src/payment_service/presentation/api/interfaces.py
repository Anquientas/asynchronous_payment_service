from typing import Protocol

from payment_service.application.use_cases.create_payment import CreatePayment
from payment_service.application.use_cases.get_payment import GetPayment


class UseCaseProvider(Protocol):
    def create_payment(self) -> CreatePayment: ...

    def get_payment(self) -> GetPayment: ...
