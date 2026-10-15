from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid7

from payment_service.domain.constants import (
    Currency,
    ErrorMessage,
    PaymentStatus,
)
from payment_service.domain.exceptions import (
    InvalidAmountError,
    InvalidStatusTransitionError,
)


@dataclass
class Payment:
    id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    webhook_url: str
    idempotency_key: str
    created_at: datetime
    processed_at: datetime | None = None

    def _check_status_is_pending(self) -> None:
        if self.status != PaymentStatus.PENDING:
            raise InvalidStatusTransitionError(
                ErrorMessage.INCORRECT_CHANGE_STATUS.format(
                    status=self.status,
                )
            )

    def _end_payment_processing(self, status: PaymentStatus) -> None:
        self.status = status
        self.processed_at = _current_time()

    @classmethod
    def create(
        cls,
        amount: Decimal,
        currency: Currency,
        description: str,
        metadata: dict[str, Any],
        idempotency_key: str,
        webhook_url: str,
    ) -> Payment:
        if amount <= 0:
            raise InvalidAmountError(
                ErrorMessage.INCORRECT_AMOUNT.format(
                    amount=amount,
                )
            )
        return cls(
            id=uuid7(),
            status=PaymentStatus.PENDING,
            created_at=_current_time(),
            amount=amount,
            currency=currency,
            description=description,
            metadata=metadata,
            idempotency_key=idempotency_key,
            webhook_url=webhook_url,
        )

    def mark_succeeded(self) -> None:
        self._check_status_is_pending()
        self._end_payment_processing(status=PaymentStatus.SUCCEEDED)

    def mark_failed(self) -> None:
        self._check_status_is_pending()
        self._end_payment_processing(status=PaymentStatus.FAILED)


def _current_time() -> datetime:
    return datetime.now(UTC)
