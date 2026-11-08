from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.pipeline.types import Article, NewsItem
from app.themes import Theme

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 8, 15, 0, tzinfo=UTC)


@pytest.fixture
def theme() -> Theme:
    return Theme(
        id="futebol",
        nome="Futebol",
        icone="⚽",
        cor="#22C55E",
        busca="futebol",
        bloqueadas=["apostas", "bet", "palpite"],
    )


@pytest.fixture
def article() -> Article:
    return Article(
        title="Time A vence clássico e assume a liderança",
        url="https://ge.globo.com/x",
        source="ge",
        published=NOW,
        text="O Time A venceu o clássico neste domingo. " * 40,
    )


def make_item(title: str, hours_ago: float, link: str | None = None, summary: str = "") -> NewsItem:
    from datetime import timedelta

    return NewsItem(
        title=title,
        link=link or f"https://news.google.com/rss/articles/{abs(hash(title))}",
        published=NOW - timedelta(hours=hours_ago),
        source="ge",
        summary=summary,
    )
