"""FastAPI: app, CORS, erros no formato padrão e startup (banco, voz, agendador)."""

from __future__ import annotations

import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import init_db
from app.pipeline.podia_tts import base as tts
from app.routes import router
from app.settings import get_settings

log = logging.getLogger("podia")


def _load_voice() -> None:
    try:
        tts.get_engine()
        log.info("motor de voz carregado")
    except Exception:
        log.exception("falha ao carregar o motor de voz")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    s = get_settings()
    logging.basicConfig(level=s.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db()
    scheduler = None
    if s.scheduler_enabled:
        # Carrega o modelo uma vez, em segundo plano, para a API subir na hora.
        threading.Thread(target=_load_voice, name="carregar-voz", daemon=True).start()
        from app.scheduler import build_scheduler

        scheduler = build_scheduler()
        scheduler.start()
        log.info("agendador ligado: a cada %sh", s.scheduler_interval_hours)
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="podIA API",
    description="Notícia em 2 minutos, em diálogo, gerada por IA.",
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if not (isinstance(detail, dict) and "erro" in detail):
        detail = {"erro": f"http_{exc.status_code}", "mensagem": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=detail)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422, content={"erro": "parametro_invalido", "mensagem": str(exc.errors()[:3])}
    )
