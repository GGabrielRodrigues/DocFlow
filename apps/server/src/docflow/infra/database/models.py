from datetime import datetime
from typing import Annotated
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

Id = Annotated[str, mapped_column(String(36), primary_key=True)]


class Base(DeclarativeBase):
    pass


class InstitutionModel(Base):
    __tablename__ = "institutions"
    __table_args__ = (UniqueConstraint("cnpj", name="uq_institutions_cnpj"),)

    id: Mapped[Id] = mapped_column(default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(500))
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


class UserModel(TenantScopedMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("institution_id", "email", name="uq_users_institution_email"),
    )

    id: Mapped[Id] = mapped_column(default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
