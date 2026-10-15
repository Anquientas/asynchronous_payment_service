from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from payment_service.domain.constants import Currency


@dataclass
class CreatePaymentInputDTO:
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    idempotency_key: str
    webhook_url: str
