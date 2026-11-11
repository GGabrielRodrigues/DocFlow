from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Mapped, Session, mapped_column

from docflow.infra.database.models import Base, TenantScopedMixin
from docflow.infra.database.repository import TenantRepository


class TenantDocument(TenantScopedMixin, Base):
    __tablename__ = "test_documents"

    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()


def test_tenant_repository_does_not_read_another_tenant() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    institution_a = str(uuid4())
    institution_b = str(uuid4())

    with Session(engine) as session:
        session.add_all(
            [
                TenantDocument(
                    id="document-a",
                    institution_id=institution_a,
                    title="Tenant A",
                ),
                TenantDocument(
                    id="document-b",
                    institution_id=institution_b,
                    title="Tenant B",
                ),
            ]
        )
        session.commit()

        tenant_a = TenantRepository(session, TenantDocument, institution_a)
        assert [document.title for document in tenant_a.list()] == ["Tenant A"]
        assert tenant_a.get("document-b") is None
