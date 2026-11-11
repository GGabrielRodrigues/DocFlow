from typing import TypeVar, cast

from sqlalchemy import Select, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from docflow.infra.database.models import Base, TenantScopedMixin

ModelT = TypeVar("ModelT", bound=Base)


class TenantRepository[ModelT: Base]:
    def __init__(
        self,
        session: Session,
        model: type[ModelT],
        institution_id: str,
    ) -> None:
        if not issubclass(model, TenantScopedMixin):
            raise TypeError("TenantRepository requires a tenant-scoped model")

        self.session: Session = session
        self.model: type[ModelT] = model
        self.institution_id: str = institution_id

    def statement(self) -> Select[tuple[ModelT]]:
        institution_column = cast(
            InstrumentedAttribute[str],
            getattr(self.model, "institution_id"),  # noqa: B009
        )
        statement = select(self.model).where(
            institution_column == self.institution_id,
        )
        return cast(Select[tuple[ModelT]], statement)

    def list(self) -> list[ModelT]:
        return list(self.session.scalars(self.statement()))

    def get(self, record_id: str) -> ModelT | None:
        id_column = cast(
            InstrumentedAttribute[str],
            getattr(self.model, "id"),  # noqa: B009
        )
        statement = self.statement().where(id_column == record_id)
        return cast(ModelT | None, self.session.scalar(statement))
