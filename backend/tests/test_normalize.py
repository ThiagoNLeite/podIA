from __future__ import annotations

import pytest

from app.pipeline.podia_tts.normalize import apply_dictionary, normalize_numbers, normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("venceu por 2x1", "venceu por dois a um"),
        ("placar de 3 x 0", "placar de três a zero"),
        ("alta de 15%", "alta de quinze por cento"),
        ("alta de 1,5%", "alta de um vírgula cinco por cento"),
        ("contrato de R$ 1,5 mi", "contrato de um vírgula cinco milhão de reais"),
        ("R$ 3 bilhões", "três bilhões de reais"),
        ("R$ 300 mil", "trezentos mil reais"),
        ("custa R$ 25", "custa vinte e cinco reais"),
        ("custa R$ 25,90", "custa vinte e cinco reais e noventa centavos"),
        ("às 18h", "às dezoito horas"),
        ("às 18h30", "às dezoito e trinta"),
        ("no 2º semestre", "no segundo semestre"),
        ("a 3ª rodada", "a terceira rodada"),
        ("em 2026", "em dois mil e vinte e seis"),
        ("1.500 torcedores", "mil e quinhentos torcedores"),
    ],
)
def test_numbers(raw: str, expected: str) -> None:
    assert normalize_numbers(raw) == expected


def test_vasco_x_palmeiras_is_not_a_score() -> None:
    assert normalize_numbers("Vasco x Palmeiras") == "Vasco x Palmeiras"


def test_dictionary_siglas_are_case_sensitive_and_whole_word() -> None:
    siglas = {"STF": "ésse tê éfe", "PT": "pê tê"}
    assert apply_dictionary("O STF decidiu", siglas, {}) == "O ésse tê éfe decidiu"
    assert apply_dictionary("O PT e o PTB", siglas, {}) == "O pê tê e o PTB"
    assert apply_dictionary("pt e stf", siglas, {}) == "pt e stf"


def test_dictionary_names_ignore_case() -> None:
    assert apply_dictionary("a NETFLIX e a Netflix", {}, {"Netflix": "nétflics"}) == "a nétflics e a nétflics"


def test_normalize_text_uses_pronuncia_yaml() -> None:
    out = normalize_text("Segundo o STF, a Crunchyroll pagou R$ 2 mi.")
    assert out == "Segundo o ésse tê éfe, a cránchi rôu pagou dois milhões de reais."
