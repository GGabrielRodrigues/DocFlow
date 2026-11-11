from datetime import datetime
from typing import Annotated
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

Id = Annotated[str, mapped_column(String(36), primary_key=True)]


class Base(DeclarativeBase):
    pass


class InstitutionModel(Base):
    __tablename__ = "institutions"

    id: Mapped[Id] = mapped_column(default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


class TenantScopedMixin:
    @declared_attr
    def institution_id(cls) -> Mapped[str]:
        return mapped_column(
            String(36),
            ForeignKey("institutions.id"),
            nullable=False,
            index=True,
        )
