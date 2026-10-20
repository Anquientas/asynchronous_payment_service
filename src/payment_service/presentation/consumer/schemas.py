from uuid import UUID

from pydantic import BaseModel


class PaymentCreatedMessage(BaseModel):
    payment_id: UUID
