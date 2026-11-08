from __future__ import annotations

import json

import pytest

from app.pipeline.dialogue import base
from app.pipeline.dialogue.base import DialogueError, generate_dialogue, generate_with, parse_and_validate
from app.pipeline.dialogue.local import generate_local

FILLER = "a partida terminou com vitória do time da casa diante de um estádio lotado e animado"  # 16 palavras


def make_json(n_lines: int = 11, words_per_line: int = 26, first: str = "dora", extra: str = "") -> str:
    falas = []
    for i in range(n_lines):
        voz = first if i % 2 == 0 else ("alex" if first == "dora" else "dora")
        words = (FILLER + " ") * 3
        texto = " ".join(words.split()[:words_per_line]) + "."
        if i == 3 and extra:
            texto += " " + extra
        falas.append({"voz": voz, "texto": texto})
    return json.dumps({"titulo_episodio": "Time A vence clássico", "falas": falas}, ensure_ascii=False)


class FakeProvider:
    def __init__(self, responses: list[str | Exception], name: str = "fake") -> None:
        self.name = name
        self.responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_valid_dialogue_passes() -> None:
    d = parse_and_validate(make_json())
    assert len(d.falas) == 11 and d.word_count == 286


def test_accepts_code_fence() -> None:
    assert parse_and_validate(f"```json\n{make_json()}\n```").titulo_episodio


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("isto não é json", "JSON válido"),
        (make_json().replace('"alex"', '"bob"'), "esquema"),
        (make_json(first="alex"), "primeira fala"),
        (make_json(n_lines=6, words_per_line=45), "6 falas"),
        (make_json(words_per_line=15), "faltam"),
        (make_json(words_per_line=40), "corte"),
        (make_json(extra="veja em https://ge.globo.com"), "URL"),
        (make_json(extra="que golaço 🔥"), "emoji"),
        (make_json(extra="**importante**"), "Markdown"),
        (make_json(extra="nao sei, a materia diz"), "acentos"),
    ],
)
def test_invalid_dialogues(raw: str, message: str) -> None:
    with pytest.raises(DialogueError, match=message):
        parse_and_validate(raw)


def test_title_max_90_chars() -> None:
    raw = json.loads(make_json())
    raw["titulo_episodio"] = "x" * 91
    with pytest.raises(DialogueError, match="titulo_episodio"):
        parse_and_validate(json.dumps(raw))


def test_retry_appends_error_to_prompt() -> None:
    p = FakeProvider([make_json(words_per_line=10), make_json()])
    d = generate_with(p, "PROMPT", sleep=lambda s: None)
    assert d.gerador == "fake"
    assert len(p.prompts) == 2
    assert "rejeitada" in p.prompts[1] and "faltam" in p.prompts[1]


def test_gives_up_after_two_extra_attempts() -> None:
    p = FakeProvider(["ruim"] * 3)
    with pytest.raises(DialogueError):
        generate_with(p, "PROMPT", sleep=lambda s: None)
    assert len(p.prompts) == 3


def test_transient_error_waits_and_calls_again() -> None:
    waits: list[float] = []
    p = FakeProvider([RuntimeError("503 UNAVAILABLE"), make_json()])
    assert generate_with(p, "PROMPT", sleep=waits.append).gerador == "fake"
    assert waits == [base.BACKOFF_S[0]]


def test_non_transient_error_is_not_retried() -> None:
    p = FakeProvider([RuntimeError("404 NOT_FOUND"), make_json()])
    with pytest.raises(RuntimeError):
        generate_with(p, "PROMPT", sleep=lambda s: None)


def test_chain_falls_to_next_provider_then_local(theme, article, monkeypatch) -> None:
    monkeypatch.setattr(base.time, "sleep", lambda s: None)
    broken = FakeProvider([RuntimeError("401 bad key")], name="gemini")
    good = FakeProvider([make_json()], name="groq")
    assert generate_dialogue(theme, article, [broken, good]).gerador == "groq"

    all_bad = [FakeProvider(["ruim"] * 3, name="gemini"), FakeProvider([RuntimeError("x")], name="groq")]
    assert generate_dialogue(theme, article, all_bad).gerador == "local"


def test_prompt_contains_article_and_rules(theme, article) -> None:
    prompt = base.build_prompt(theme, article)
    assert article.title in prompt and "ge" in prompt and "Futebol" in prompt
    assert "SOMENTE informações presentes na matéria" in prompt


def test_local_generator_is_valid_without_length_rules(theme, article) -> None:
    article.text = (
        "Time A vence clássico e assume a liderança\n"
        "Subtítulo sem ponto final\n"
        "O Time A venceu o Time B por dois a um neste domingo no estádio Municipal.\n"
        "O gol da vitória foi marcado nos minutos finais pelo zagueiro João, de cabeça."
    )
    d = generate_local(theme, article)
    assert d.gerador == "local" and d.falas[0].voz == "dora" and d.falas[-1].voz == "dora"
    joined = " ".join(f.texto for f in d.falas)
    assert "venceu o Time B" in joined and "Subtítulo" not in joined
    parse_and_validate(d.model_dump_json(exclude={"gerador"}), strict_length=False)


def test_accepts_longest_short_attempt_when_only_length_fails() -> None:
    p = FakeProvider(
        [make_json(words_per_line=18), make_json(words_per_line=21), make_json(words_per_line=19)]
    )
    d = generate_with(p, "PROMPT", sleep=lambda s: None)
    assert d.word_count == 11 * 21 and d.gerador == "fake"


def test_too_short_attempts_still_fail() -> None:
    p = FakeProvider([make_json(words_per_line=12)] * 3)
    with pytest.raises(DialogueError):
        generate_with(p, "PROMPT", sleep=lambda s: None)
