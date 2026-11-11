from collections.abc import Generator
from functools import lru_cache
from typing import Any

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from docflow.core.config import Settings, get_settings


@lru_cache(maxsize=4)
def get_engine(database_url: str) -> Engine:
    connect_args: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, connect_args=connect_args)


def get_db_session(
    settings: Settings = Depends(get_settings),
) -> Generator[Session, None, None]:
    engine = get_engine(settings.database_url)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with session_factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
