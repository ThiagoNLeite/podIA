"""Fase 0: gera 1 episódio completo pela linha de comando, sem API e sem banco.

Uso (em backend/):
    .venv/Scripts/python scripts/poc_episodio.py --tema futebol --saida futebol.mp3
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline import audio, news
from app.pipeline.dialogue.base import generate_dialogue
from app.pipeline.podia_tts.base import get_engine, synthesize
from app.themes import get_theme


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera um episódio do podIA")
    ap.add_argument("--tema", default="futebol")
    ap.add_argument("--saida", type=Path, default=None)
    ap.add_argument("--sem-ia", action="store_true", help="usa só o gerador local")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    theme = get_theme(args.tema)
    out = args.saida or Path(f"{theme.id}.mp3")
    timings: dict[str, float] = {}

    def step(name: str, t0: float) -> None:
        timings[name] = round(time.perf_counter() - t0, 1)
        print(f"  ⏱  {name}: {timings[name]}s")

    print(f"\n▶ Tema: {theme.icone} {theme.nome}")
    t = time.perf_counter()
    article = news.find_article(theme)
    step("notícia", t)
    if article is None:
        print("✗ Nenhuma notícia válida encontrada.")
        return 1
    print(f"  📰 {article.title} — {article.source} ({article.word_count} palavras)\n  🔗 {article.url}")

    t = time.perf_counter()
    dialogue = generate_dialogue(theme, article, providers=[] if args.sem_ia else None)
    step("diálogo", t)
    print(f"  🎙  gerador: {dialogue.gerador} · {len(dialogue.falas)} falas · {dialogue.word_count} palavras")
    print(f"  📝 {dialogue.titulo_episodio}\n")
    for f in dialogue.falas:
        print(f"     {f.voz.upper():5} {f.texto}")

    t = time.perf_counter()
    engine = get_engine()
    step("carregar voz", t)
    t = time.perf_counter()
    segments = synthesize(dialogue, engine)
    step("vozes", t)

    t = time.perf_counter()
    result = audio.assemble(segments, out)
    step("montagem", t)

    meta = {
        "titulo": dialogue.titulo_episodio,
        "gerador": dialogue.gerador,
        "motor_voz": engine.name,
        "duracao_s": result.duration_s,
        "fonte": {"veiculo": article.source, "titulo": article.title, "url": article.url,
                  "publicada_em": article.published.isoformat()},
        "falas": [{"voz": f.voz, "texto": f.texto, "inicio_s": s}
                  for f, s in zip(dialogue.falas, result.line_starts, strict=True)],
        "tempos_s": timings,
    }  # fmt: skip
    out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    mins, secs = divmod(int(result.duration_s), 60)
    print(f"\n✓ {out} — duração {mins}:{secs:02d} · geração total {sum(timings.values()):.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
