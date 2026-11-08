from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import db
from app.models import Episodio, Noticia
from app.pipeline import audio, run
from app.pipeline.types import Article, Dialogue, Line
from app.settings import get_settings

ADMIN = "chave-de-teste"


class SilentEngine:
    """Motor de voz falso: 0,5 s de silêncio por fala."""

    name = "fake"
    sample_rate = 24_000

    def synthesize(self, text: str, voice: str) -> np.ndarray:
        return np.zeros(self.sample_rate // 2, dtype=np.float32)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("ADMIN_KEY", ADMIN)
    monkeypatch.setenv("TZ", "America/Cuiaba")
    get_settings.cache_clear()
    db.get_engine.cache_clear()
    run.state.generating.clear()
    run.state.last_error.clear()
    run.state.last_cycle.clear()
    db.init_db()
    yield
    db.get_engine().dispose()
    get_settings.cache_clear()
    db.get_engine.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as c:
        yield c


def add_episode(theme: str = "futebol", audio_file: str | None = "futebol_1.mp3", **kw) -> Episodio:
    with Session(db.get_engine()) as s:
        n = Noticia(
            tema=theme,
            titulo="Time A vence clássico",
            url=f"https://ge.globo.com/{theme}/{datetime.now().timestamp()}",
            veiculo="ge",
            publicada_em=datetime(2026, 11, 8, 11, 30, tzinfo=UTC),
        )
        s.add(n)
        s.commit()
        s.refresh(n)
        falas = [{"voz": "dora", "texto": "Oi, eu sou a Dora!", "inicio_s": 0.0}]
        ep = Episodio(
            tema=theme,
            noticia_id=n.id or 0,
            titulo="Time A assume a liderança",
            dialogo_json=json.dumps({"falas": falas}),
            gerador=kw.pop("gerador", "gemini"),
            motor_voz="kokoro",
            audio_arquivo=audio_file,
            duracao_s=118,
            gerado_em=kw.pop("gerado_em", datetime(2026, 11, 8, 13, 4, 12, tzinfo=UTC)),
            **kw,
        )
        s.add(ep)
        s.commit()
        s.refresh(ep)
        return ep


# ---------- rotas ----------


def test_themes_lists_six_with_last_episode_time(client) -> None:
    add_episode("futebol")
    body = client.get("/themes").json()
    assert [t["id"] for t in body] == ["futebol", "anime", "filmes", "politica", "tecnologia", "automotivo"]
    futebol = body[0]
    assert futebol == {
        "id": "futebol",
        "nome": "Futebol",
        "icone": "⚽",
        "cor": "#22C55E",
        "ultimo_episodio_em": "2026-11-08T09:04:12-04:00",  # UTC -> America/Cuiaba
    }
    assert body[1]["ultimo_episodio_em"] is None


def test_latest_episode_200_matches_spec(client) -> None:
    ep = add_episode()
    r = client.get("/episodes/latest", params={"theme": "futebol"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == ep.id
    assert body["audio_url"] == "/audio/futebol_1.mp3"
    assert body["gerador"] == "gemini"
    assert body["fonte"]["veiculo"] == "ge"
    assert body["fonte"]["publicada_em"] == "2026-11-08T07:30:00-04:00"
    assert body["falas"] == [{"voz": "dora", "texto": "Oi, eu sou a Dora!", "inicio_s": 0.0}]
    assert body["aviso"].startswith("Episódio gerado por IA")


def test_latest_returns_newest_ready_episode(client) -> None:
    add_episode(gerado_em=datetime(2026, 11, 8, 10, tzinfo=UTC))
    newest = add_episode(gerado_em=datetime(2026, 11, 8, 13, tzinfo=UTC))
    add_episode(gerado_em=datetime(2026, 11, 8, 14, tzinfo=UTC), status="erro")
    assert client.get("/episodes/latest?theme=futebol").json()["id"] == newest.id


def test_local_generator_has_its_own_notice(client) -> None:
    add_episode(gerador="local")
    assert "sem IA" in client.get("/episodes/latest?theme=futebol").json()["aviso"]


def test_latest_without_episode_starts_generation_and_returns_202(client, monkeypatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(run, "start_in_background", lambda t, force=False: started.append(t) or True)
    r = client.get("/episodes/latest?theme=anime")
    assert r.status_code == 202
    assert r.json() == {"status": "gerando", "tema": "anime", "tentar_novamente_em_s": 5}
    assert started == ["anime"]


def test_latest_while_generating_does_not_start_again(client, monkeypatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(run, "start_in_background", lambda t, force=False: started.append(t) or True)
    run.state.generating.add("anime")
    assert client.get("/episodes/latest?theme=anime").status_code == 202
    assert started == []


def test_latest_failed_generation_returns_503_once_then_retries(client, monkeypatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(run, "start_in_background", lambda t, force=False: started.append(t) or True)
    run.state.last_error["anime"] = "noticia: sem internet"
    r = client.get("/episodes/latest?theme=anime")
    assert r.status_code == 503
    assert r.json()["erro"] == "geracao_falhou"
    assert client.get("/episodes/latest?theme=anime").status_code == 202  # "Tentar de novo"
    assert started == ["anime"]


def test_unknown_theme_and_episode_404(client) -> None:
    r = client.get("/episodes/latest?theme=culinaria")
    assert r.status_code == 404 and r.json()["erro"] == "tema_inexistente"
    r = client.get("/episodes/999")
    assert r.status_code == 404 and r.json()["erro"] == "episodio_inexistente"


def test_episode_by_id(client) -> None:
    ep = add_episode()
    assert client.get(f"/episodes/{ep.id}").json()["titulo"] == "Time A assume a liderança"


def test_audio_supports_range(client) -> None:
    (get_settings().audio_dir / "futebol_1.mp3").write_bytes(b"ID3" + bytes(5000))
    full = client.get("/audio/futebol_1.mp3")
    assert full.status_code == 200 and full.headers["content-type"] == "audio/mpeg"
    assert full.headers.get("accept-ranges") == "bytes"
    part = client.get("/audio/futebol_1.mp3", headers={"Range": "bytes=100-199"})
    assert part.status_code == 206 and len(part.content) == 100


def test_audio_404_and_path_traversal(client) -> None:
    assert client.get("/audio/nao_existe.mp3").status_code == 404
    assert client.get("/audio/..%2Fpodia.db").status_code == 404


def test_admin_requires_key(client, monkeypatch) -> None:
    started: list[tuple[str, bool]] = []
    monkeypatch.setattr(run, "start_in_background", lambda t, force=False: started.append((t, force)) or True)
    assert client.post("/admin/generate?theme=futebol").status_code == 401
    r = client.post("/admin/generate?theme=futebol", headers={"X-Admin-Key": "errada"})
    assert r.status_code == 401 and r.json()["erro"] == "nao_autorizado"
    r = client.post("/admin/generate?theme=futebol", headers={"X-Admin-Key": ADMIN})
    assert r.status_code == 202
    assert started == [("futebol", True)]


def test_health(client) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["motor_voz"] == "kokoro"
    assert body["gerando"] == [] and body["ultimo_ciclo"] is None


def test_docs_available(client) -> None:
    assert client.get("/docs").status_code == 200
    assert "/episodes/latest" in client.get("/openapi.json").json()["paths"]


# ---------- orquestrador ----------


def _article(url: str = "https://ge.globo.com/materia-1") -> Article:
    return Article(
        title="Time A vence clássico",
        url=url,
        source="ge",
        published=datetime(2026, 11, 8, 12, tzinfo=UTC),
        text="O Time A venceu. " * 100,
    )


def _dialogue(*args) -> Dialogue:
    return Dialogue(
        titulo_episodio="Time A lidera",
        falas=[Line(voz="dora", texto="Oi, eu sou a Dora!"), Line(voz="alex", texto="E eu sou o Alex.")],
        gerador="gemini",
    )


@pytest.fixture
def pipeline(monkeypatch):
    try:
        audio.find_ffmpeg()
    except FileNotFoundError:
        pytest.skip("ffmpeg não instalado")
    monkeypatch.setattr(run, "generate_dialogue", _dialogue)
    monkeypatch.setattr(get_settings(), "assets_dir", get_settings().data_path)  # sem vinheta


def _find(articles: list[Article | None]):
    def find(theme, used):
        for a in articles:
            if a is None or a.url not in used:
                return a
        return None

    return find


def test_run_theme_creates_ready_episode_with_line_times(pipeline) -> None:
    ep = run.run_theme("futebol", find_article=_find([_article()]), engine=SilentEngine())
    assert ep is not None and ep.status == "pronto"
    assert ep.audio_arquivo == f"futebol_{ep.id}.mp3"
    assert (get_settings().audio_dir / ep.audio_arquivo).exists()
    falas = json.loads(ep.dialogo_json)["falas"]
    assert [f["inicio_s"] for f in falas] == [0.0, 0.8]  # 0,5 s de fala + 0,3 s de pausa
    assert ep.motor_voz == "fake" and ep.gerador == "gemini"


def test_run_theme_skips_already_used_news_unless_forced(pipeline) -> None:
    find = _find([_article()])
    assert run.run_theme("futebol", find_article=find, engine=SilentEngine())
    assert run.run_theme("futebol", find_article=find, engine=SilentEngine()) is None  # sem notícia nova
    forced = run.run_theme("futebol", force=True, find_article=find, engine=SilentEngine())
    assert forced is not None
    with Session(db.get_engine()) as s:
        assert len(s.exec(select(Noticia)).all()) == 1  # reaproveitou a notícia


def test_run_theme_error_is_recorded(pipeline, monkeypatch) -> None:
    def broken(*args):
        raise RuntimeError("ffmpeg quebrou")

    monkeypatch.setattr(run.audio, "assemble", broken)
    assert run.run_theme("futebol", find_article=_find([_article()]), engine=SilentEngine()) is None
    assert run.state.last_error["futebol"].startswith("montagem")
    with Session(db.get_engine()) as s:
        ep = s.exec(select(Episodio)).one()
        assert ep.status == "erro" and "ffmpeg quebrou" in (ep.erro or "")


def test_lock_prevents_two_generations_of_same_theme(pipeline) -> None:
    lock = run.state.lock_for("futebol")
    lock.acquire()
    try:
        assert run.run_theme("futebol", find_article=_find([_article()]), engine=SilentEngine()) is None
    finally:
        lock.release()


def test_run_all_only_missing(pipeline, monkeypatch) -> None:
    add_episode("futebol")
    calls: list[str] = []
    monkeypatch.setattr(run, "run_theme", lambda t, force=False: calls.append(t) or None)
    results = run.run_all(only_missing=True)
    assert results["futebol"] == "ja_existe"
    assert calls == ["anime", "filmes", "politica", "tecnologia", "automotivo"]
    assert run.state.last_cycle["resultados"] == results


def test_cleanup_removes_old_audio_but_keeps_record() -> None:
    from app.scheduler import cleanup_old_audio

    path = get_settings().audio_dir / "futebol_1.mp3"
    path.write_bytes(b"x")
    old = add_episode(gerado_em=datetime.now(UTC) - timedelta(days=8))
    add_episode(audio_file="futebol_2.mp3", gerado_em=datetime.now(UTC))
    assert cleanup_old_audio() == 1
    assert not path.exists()
    with Session(db.get_engine()) as s:
        assert s.get(Episodio, old.id).audio_arquivo is None  # type: ignore[union-attr]
