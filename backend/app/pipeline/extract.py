"""Etapa 2: resolver o link do Google News e extrair o corpo da matéria (§4.2)."""

from __future__ import annotations

import logging
import re
import unicodedata

import httpx
import trafilatura

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
TIMEOUT_S = 10


def resolve_url(link: str) -> str | None:
    """Converte news.google.com/rss/articles/... na URL real do portal."""
    if "news.google.com" not in link:
        return link
    from googlenewsdecoder import gnewsdecoder

    try:
        res = gnewsdecoder(link, interval=1)
    except Exception as exc:  # noqa: BLE001 — biblioteca externa instável
        log.warning("decode falhou: %s", exc)
        return None
    if not res.get("success"):
        log.warning("decode falhou: %s", res.get("message"))
        return None
    return res["decoded_url"]


def download_html(url: str) -> str | None:
    try:
        resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("download falhou (%s): %s", url, exc)
        return None
    return resp.text


def extract_text(html: str) -> str:
    """Só o corpo da matéria, sem menus, anúncios e comentários."""
    return trafilatura.extract(html, include_comments=False, include_tables=False) or ""


def extract_article(url: str) -> str | None:
    html = download_html(url)
    if html is None:
        return None
    text = extract_text(html)
    return text or None


def _norm_words(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z0-9]+", s) if len(w) > 3}


def text_matches_title(title: str, text: str, min_ratio: float = 0.4) -> bool:
    """Confere se o texto extraído é mesmo da matéria (às vezes vem outro artigo da página)."""
    title_words = _norm_words(title)
    if not title_words:
        return True
    text_words = _norm_words(text[:3000])
    return len(title_words & text_words) / len(title_words) >= min_ratio
