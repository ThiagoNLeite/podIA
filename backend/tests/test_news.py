from __future__ import annotations

from app.pipeline import extract, news
from app.themes import load_themes
from tests.conftest import FIXTURES, NOW, make_item

LONG_TEXT = "Time A vence clássico e assume a liderança do campeonato. " + "palavra " * 300


def test_parse_feed_strips_source_and_reads_dates() -> None:
    items = news.parse_feed((FIXTURES / "google_news.xml").read_bytes())
    assert len(items) == 4
    first = items[0]
    assert first.title == "Time A vence clássico e assume a liderança"
    assert first.source == "ge"
    assert first.published.isoformat() == "2026-11-08T12:00:00+00:00"
    assert first.summary == ""  # resumo do Google News é só HTML com links


def test_filter_window_24h_72h_and_sorting() -> None:
    items = news.parse_feed((FIXTURES / "google_news.xml").read_bytes())
    day = news.filter_window(items, 24, now=NOW)
    assert [i.source for i in day] == ["LANCE!", "ge"]  # mais recente primeiro
    three_days = news.filter_window(items, 72, now=NOW)
    assert [i.source for i in three_days] == ["LANCE!", "ge", "Estadão"]


def test_never_more_than_72h_even_if_window_bigger() -> None:
    items = [make_item("antiga", 80), make_item("recente", 2)]
    assert [i.title for i in news.filter_window(items, 200, now=NOW)] == ["recente"]


def test_blocked_words_ignore_accents_case_and_partial_words(theme) -> None:
    assert news.is_blocked(make_item("Casa de APOSTAS patrocina torneio", 1), theme.bloqueadas)
    assert news.is_blocked(make_item("Palpité do dia", 1), theme.bloqueadas)  # sem acento
    assert news.is_blocked(make_item("Título normal", 1, summary="site de bet"), theme.bloqueadas)
    assert not news.is_blocked(make_item("Alfabeto e beterraba", 1), theme.bloqueadas)


def _select(theme, items, texts: dict[str, str], used: set[str] | None = None):
    def resolve(link: str) -> str:
        return link.replace("news.google.com/rss/articles", "portal.com.br")

    return news.select_news(theme, items, used, resolve=resolve, get_text=texts.get)


def test_select_skips_blocked_repeated_and_short(theme) -> None:
    items = [
        make_item("Aposta: bet do dia", 1, link="https://news.google.com/rss/articles/a"),
        make_item("Time A vence clássico e assume a liderança", 2, link="https://news.google.com/rss/articles/b"),
        make_item("Time A vence clássico e assume a liderança", 3, link="https://news.google.com/rss/articles/c"),
        make_item("Time A vence clássico e assume a liderança", 4, link="https://news.google.com/rss/articles/d"),
    ]  # fmt: skip
    texts = {
        "https://portal.com.br/b": LONG_TEXT,  # já usada
        "https://portal.com.br/c": "Time A vence clássico, texto curto.",
        "https://portal.com.br/d": LONG_TEXT,
    }
    art = _select(theme, items, texts, used={"https://portal.com.br/b"})
    assert art is not None and art.url == "https://portal.com.br/d"


def test_select_rejects_text_from_another_article(theme) -> None:
    items = [
        make_item("Grêmio garante vaga na Libertadores", 1, link="https://news.google.com/rss/articles/x")
    ]
    texts = {"https://portal.com.br/x": "Clubes antecipam receitas de ingresso. " * 60}
    assert _select(theme, items, texts) is None


def test_select_tests_at_most_8_candidates(theme) -> None:
    calls: list[str] = []
    items = [make_item(f"Notícia {i}", i) for i in range(12)]
    news.select_news(theme, items, resolve=lambda link: calls.append(link) or None)
    assert len(calls) == news.MAX_CANDIDATES


def test_select_skips_portugal_domains(theme) -> None:
    items = [make_item("Time A vence clássico e assume a liderança", 1, link="https://jornal.pt/a")]
    art = news.select_news(theme, items, resolve=lambda link: link, get_text=lambda url: LONG_TEXT)
    assert art is None


def test_find_article_widens_to_72h(theme, monkeypatch) -> None:
    windows: list[int] = []
    monkeypatch.setattr(news, "fetch_candidates", lambda t, w: windows.append(w) or [])
    assert news.find_article(theme) is None
    assert windows == [24, 72]


def test_google_news_url_uses_when_filter() -> None:
    assert "when%3A1d" in news.google_news_url("futebol", 24)
    assert "when%3A3d" in news.google_news_url("futebol", 72)


def test_extract_text_ignores_menus_and_footer() -> None:
    text = extract.extract_text((FIXTURES / "artigo.html").read_text(encoding="utf-8"))
    assert "venceu o Time B" in text
    assert "Assine já" not in text and "Todos os direitos" not in text


def test_text_matches_title() -> None:
    assert extract.text_matches_title(
        "Grêmio garante vaga na Libertadores", "O Grêmio garantiu a vaga na Libertadores..."
    )
    assert not extract.text_matches_title("Grêmio garante vaga na Libertadores", "Clubes antecipam receitas.")


def test_themes_yaml_has_six_valid_themes() -> None:
    themes = load_themes()
    assert list(themes) == ["futebol", "anime", "filmes", "politica", "tecnologia", "automotivo"]
    assert themes["anime"].janela_horas == 72
    assert themes["politica"].tom == "neutro"
