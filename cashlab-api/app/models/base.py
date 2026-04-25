
"""
CashLab — Base model mixins

Mixins reutilizáveis para todos os modelos:
- TimestampMixin: created_at, updated_at
- SoftDeleteMixin: deleted_at (nunca DELETE em registros financeiros)
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds created_at and updated_at to any model"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
        default=None,
    )


class SoftDeleteMixin:
    """Adds soft delete capability — never DELETE financial records"""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
