"""Engine SQLite + sessão."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Episodio, Noticia
from app.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    path = get_settings().data_path / "podia.db"
    return create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Iterator[Session]:
    """Dependência do FastAPI."""
    with Session(get_engine()) as session:
        yield session


def latest_episode(session: Session, theme_id: str) -> Episodio | None:
    stmt = (
        select(Episodio)
        .where(Episodio.tema == theme_id, Episodio.status == "pronto")
        .order_by(Episodio.gerado_em.desc(), Episodio.id.desc())  # type: ignore[union-attr]
        .limit(1)
    )
    return session.exec(stmt).first()


def used_urls(session: Session, theme_id: str) -> set[str]:
    return set(session.exec(select(Noticia.url).where(Noticia.tema == theme_id)).all())
