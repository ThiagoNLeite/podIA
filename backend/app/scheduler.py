"""APScheduler: pipeline a cada N horas + limpeza diária de áudios antigos."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from app.db import get_engine
from app.models import Episodio
from app.pipeline import run
from app.settings import get_settings

log = logging.getLogger("podia.scheduler")


def cleanup_old_audio(now: datetime | None = None) -> int:
    """Apaga MP3 com mais de AUDIO_RETENTION_DAYS; o registro fica no banco com audio_arquivo = NULL."""
    s = get_settings()
    limit = (now or datetime.now(UTC)) - timedelta(days=s.audio_retention_days)
    removed = 0
    with Session(get_engine()) as session:
        old = session.exec(
            select(Episodio).where(Episodio.gerado_em < limit, Episodio.audio_arquivo.is_not(None))  # type: ignore[union-attr]
        ).all()
        for ep in old:
            path = s.audio_dir / (ep.audio_arquivo or "")
            path.unlink(missing_ok=True)
            ep.audio_arquivo = None
            session.add(ep)
            removed += 1
        session.commit()
    if removed:
        log.info("limpeza: %d áudios expirados removidos", removed)
    return removed


def build_scheduler() -> BackgroundScheduler:
    s = get_settings()
    scheduler = BackgroundScheduler(timezone=s.tz)
    scheduler.add_job(
        run.run_all,
        "interval",
        hours=s.scheduler_interval_hours,
        id="pipeline",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(cleanup_old_audio, "cron", hour=4, id="limpeza", max_instances=1)
    # Geração inicial: temas sem episódio são gerados logo após o startup.
    scheduler.add_job(
        run.run_all,
        "date",
        run_date=datetime.now(UTC) + timedelta(seconds=2),
        kwargs={"only_missing": True},
        id="geracao_inicial",
    )
    return scheduler
