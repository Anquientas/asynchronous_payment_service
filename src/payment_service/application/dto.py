from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from payment_service.domain.constants import Currency


@dataclass
class CreatePaymentInputDTO:
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    idempotency_key: str
    webhook_url: str


@dataclass
class OutboxMessage:
    message_id: UUID
    event_type: str
    payload: dict[str, Any]
    attempts: int
