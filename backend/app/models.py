from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        CheckConstraint("direction IN ('LONG', 'SHORT')", name="ck_trade_direction"),
        CheckConstraint("status IN ('open', 'closed')", name="ck_trade_status"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid4().hex[:8])
    date_open: Mapped[str] = mapped_column(String, nullable=False)
    asset: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    market: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    price_open: Mapped[float] = mapped_column(nullable=False)
    quantity: Mapped[float] = mapped_column(nullable=False)
    cost: Mapped[float] = mapped_column(nullable=False)
    stop_loss: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    date_close: Mapped[str | None] = mapped_column(String, nullable=True)
    price_close: Mapped[float | None] = mapped_column(nullable=True)
    pnl: Mapped[float | None] = mapped_column(nullable=True)
    pnl_pct: Mapped[float | None] = mapped_column(nullable=True)
    signal_source: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String, default=lambda: datetime.utcnow().isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        String, default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat()
    )


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)