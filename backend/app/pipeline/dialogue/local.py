"""Gerador local (sem IA): reserva final para o tema nunca ficar sem episódio."""

from __future__ import annotations

import re

from app.pipeline.types import Article, Dialogue, Line
from app.themes import Theme

MAX_SENTENCE_WORDS = 35


def _sentences(text: str, n: int, skip: str = "") -> list[str]:
    """Primeiras frases 'de verdade': ignora títulos/subtítulos (linhas sem pontuação final)."""
    skip_norm = " ".join(skip.lower().split())
    good: list[str] = []
    for para in text.splitlines():
        para = " ".join(para.split())
        if not para or para[-1] not in '.!?"”' or para.lower().startswith(skip_norm or "\0"):
            continue
        for p in re.split(r"(?<=[.!?])\s+", para):
            if 6 <= len(p.split()) <= MAX_SENTENCE_WORDS and not re.search(r"https?://|www\.", p):
                good.append(p.strip())
            if len(good) >= n:
                return good
    return good


def generate_local(theme: Theme, article: Article) -> Dialogue:
    base = article.summary or article.text
    s = _sentences(base, 3, skip=article.title)
    veiculo = article.source or "a fonte original"
    falas = [
        Line(voz="dora", texto="Oi, eu sou a Dora!"),
        Line(voz="alex", texto=f"E eu sou o Alex. Hoje no podIA {theme.nome}, um resumo rápido."),
        Line(voz="dora", texto=f"A notícia, segundo {veiculo}, é: {article.title.rstrip('.')}."),
    ]
    if s:
        falas.append(Line(voz="alex", texto="E o que mais a matéria conta?"))
        falas.append(Line(voz="dora", texto=" ".join(s[:2])))
    if len(s) > 2:
        falas.append(Line(voz="alex", texto=s[2]))
    falas.append(Line(voz="dora", texto=f"A matéria completa de {veiculo} está no app. Até a próxima!"))
    titulo = article.title if len(article.title) <= 90 else article.title[:87].rstrip() + "..."
    return Dialogue(titulo_episodio=titulo, falas=falas, gerador="local")
