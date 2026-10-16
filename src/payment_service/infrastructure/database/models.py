from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid7

from sqlalchemy import DateTime, Integer, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _current_datetime() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class PaymentModel(Base):
    __tablename__ = 'payments'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(String)
    metadata_: Mapped[dict[str, Any]] = mapped_column('metadata', JSONB)
    status: Mapped[str] = mapped_column(String(16))
    webhook_url: Mapped[str] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class OutboxRabbitMQModel(Base):
    __tablename__ = 'outbox'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)
    event_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_current_datetime,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
