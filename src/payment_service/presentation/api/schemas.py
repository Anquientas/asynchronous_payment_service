from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from payment_service.domain.constants import Currency, PaymentStatus


class PaymentBase(BaseModel):
    pass


class CreatePaymentRequest(PaymentBase):
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: Currency
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class ResponseBase(PaymentBase):
    model_config = ConfigDict(from_attributes=True)


class CreatePaymentResponse(ResponseBase):
    payment_id: UUID = Field(validation_alias='id')
    status: PaymentStatus
    created_at: datetime


class PaymentResponse(ResponseBase):
    payment_id: UUID = Field(validation_alias='id')
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    webhook_url: HttpUrl
    idempotency_key: str
    created_at: datetime
    processed_at: datetime | None
