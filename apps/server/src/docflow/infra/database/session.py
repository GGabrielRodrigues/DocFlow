from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from docflow.core.config import Settings


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    is_sqlite = settings.database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine_options: dict[str, object] = {"connect_args": connect_args}
    if is_sqlite and settings.database_url.endswith(":memory:"):
        engine_options["poolclass"] = StaticPool
    engine = create_engine(settings.database_url, **engine_options)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session
