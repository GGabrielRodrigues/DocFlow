from collections.abc import Generator, Iterator
from functools import lru_cache
from typing import Any

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from docflow.core.config import Settings, get_settings


@lru_cache(maxsize=16)
def get_engine(database_url: str) -> Engine:
    is_sqlite = database_url.startswith("sqlite")
    connect_args: dict[str, Any] = {"check_same_thread": False} if is_sqlite else {}
    engine_options: dict[str, Any] = {"connect_args": connect_args}
    if is_sqlite and database_url.endswith(":memory:"):
        engine_options["poolclass"] = StaticPool
    return create_engine(database_url, **engine_options)


def create_engine_from_url(database_url: str) -> Engine:
    return get_engine(database_url)


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    is_sqlite = settings.database_url.startswith("sqlite")
    if is_sqlite and settings.database_url.endswith(":memory:"):
        connect_args = {"check_same_thread": False}
        engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            poolclass=StaticPool,
        )
    else:
        engine = get_engine(settings.database_url)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session


def get_db_session(
    settings: Settings = Depends(get_settings),
) -> Generator[Session, None, None]:
    factory = create_session_factory(settings)
    with factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
