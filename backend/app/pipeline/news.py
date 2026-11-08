"""Etapa 1: buscar candidatos no RSS e escolher a notícia do episódio (§4.1)."""

from __future__ import annotations

import calendar
import logging
import re
import unicodedata
import urllib.parse
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta

import feedparser

from app.pipeline import extract
from app.pipeline.types import Article, NewsItem
from app.themes import Theme

log = logging.getLogger(__name__)

MAX_AGE_HOURS = 72
MIN_WORDS = 250  # README dizia 150; com menos que isso o diálogo de 2 min vira "enchimento"
BLOCKED_TLDS = (".pt",)  # Google News pt-BR mistura sites de Portugal
MAX_CANDIDATES = 8

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"


def google_news_url(query: str, window_hours: int) -> str:
    when = "1d" if window_hours <= 24 else f"{min(3, (window_hours + 23) // 24)}d"
    return GOOGLE_NEWS_RSS.format(q=urllib.parse.quote(f"{query} when:{when}"))


def _entry_datetime(entry: dict) -> datetime | None:
    st = entry.get("published_parsed") or entry.get("updated_parsed")
    if not st:
        return None
    return datetime.fromtimestamp(calendar.timegm(st), tz=UTC)


def parse_feed(content: str | bytes, default_source: str = "") -> list[NewsItem]:
    """Converte o XML de um RSS em NewsItems (função pura, testável com fixtures)."""
    feed = feedparser.parse(content)
    items: list[NewsItem] = []
    for e in feed.entries:
        published = _entry_datetime(e)
        if published is None or not e.get("link"):
            continue
        source = (e.get("source") or {}).get("title") or default_source or feed.feed.get("title", "")
        title = e.get("title", "").strip()
        # Google News coloca " - Veículo" no fim do título
        if source and title.endswith(f" - {source}"):
            title = title[: -len(f" - {source}")].strip()
        summary = e.get("summary", "")
        if "news.google.com" in e.link:
            summary = ""  # no Google News o resumo é só HTML com links, não serve
        items.append(NewsItem(title=title, link=e.link, published=published, source=source, summary=summary))
    return items


def fetch_feed(url: str) -> list[NewsItem]:
    feed_bytes = extract.download_html(url)
    if feed_bytes is None:
        return []
    return parse_feed(feed_bytes)


def fetch_candidates(
    theme: Theme, window_hours: int, fetch: Callable[[str], list[NewsItem]] = fetch_feed
) -> list[NewsItem]:
    """Google News + feeds extras do tema, filtrados pela janela e ordenados (mais recente primeiro)."""
    items: list[NewsItem] = []
    try:
        items += fetch(google_news_url(theme.busca, window_hours))
    except Exception as exc:  # noqa: BLE001
        log.warning("[%s] Google News falhou: %s", theme.id, exc)
    for url in theme.feeds_extras:
        try:
            items += fetch(url)
        except Exception as exc:  # noqa: BLE001
            log.warning("[%s] feed extra %s falhou: %s", theme.id, url, exc)
    return filter_window(items, window_hours)


def filter_window(
    items: Iterable[NewsItem], window_hours: int, now: datetime | None = None
) -> list[NewsItem]:
    now = now or datetime.now(UTC)
    limit = now - timedelta(hours=min(window_hours, MAX_AGE_HOURS))
    fresh = [i for i in items if limit <= i.published <= now + timedelta(minutes=30)]
    return sorted(fresh, key=lambda i: i.published, reverse=True)


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def is_blocked(item: NewsItem, blocked: list[str]) -> bool:
    haystack = f"{normalize(item.title)} {normalize(item.summary)}"
    return any(re.search(rf"\b{re.escape(normalize(b.strip()))}\b", haystack) for b in blocked if b.strip())


def select_news(
    theme: Theme,
    candidates: list[NewsItem],
    used_urls: set[str] | None = None,
    resolve: Callable[[str], str | None] = extract.resolve_url,
    get_text: Callable[[str], str | None] = extract.extract_article,
) -> Article | None:
    """Primeiro candidato válido: não bloqueado, não repetido e com texto suficiente."""
    used_urls = used_urls or set()
    tested = 0
    for item in candidates:
        if tested >= MAX_CANDIDATES:
            break
        if is_blocked(item, theme.bloqueadas):
            log.info("[%s] bloqueada: %s", theme.id, item.title)
            continue
        tested += 1
        url = resolve(item.link)
        if not url:
            continue
        host = urllib.parse.urlparse(url).hostname or ""
        if host.endswith(BLOCKED_TLDS):
            log.info("[%s] domínio fora do Brasil: %s", theme.id, host)
            continue
        if url in used_urls:
            log.info("[%s] já usada: %s", theme.id, url)
            continue
        text = get_text(url)
        words = len(text.split()) if text else 0
        if words < MIN_WORDS:
            log.info("[%s] texto curto (%d palavras): %s", theme.id, words, url)
            continue
        if not extract.text_matches_title(item.title, text):
            log.info("[%s] texto não bate com o título: %s", theme.id, url)
            continue
        return Article(
            title=item.title,
            url=url,
            source=item.source,
            published=item.published,
            text=text,
            summary=item.summary,
        )
    return None


def find_article(theme: Theme, used_urls: set[str] | None = None) -> Article | None:
    """Janela do tema (24h padrão) e, se nada servir, amplia para 72h."""
    windows = [theme.janela_horas] + ([MAX_AGE_HOURS] if theme.janela_horas < MAX_AGE_HOURS else [])
    for window in windows:
        candidates = fetch_candidates(theme, window)
        log.info("[%s] %d candidatos na janela de %dh", theme.id, len(candidates), window)
        article = select_news(theme, candidates, used_urls)
        if article:
            return article
    return None
