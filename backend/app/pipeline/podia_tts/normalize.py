"""Normalização do texto antes da síntese: números, placares, dinheiro, siglas e pronúncia."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml
from num2words import num2words

from app.settings import get_settings

LANG = "pt_BR"
MULTIPLIERS = {
    "mi": ("milhão", "milhões"),
    "milhão": ("milhão", "milhões"),
    "milhões": ("milhão", "milhões"),
    "bi": ("bilhão", "bilhões"),
    "bilhão": ("bilhão", "bilhões"),
    "bilhões": ("bilhão", "bilhões"),
    "tri": ("trilhão", "trilhões"),
    "trilhão": ("trilhão", "trilhões"),
    "trilhões": ("trilhão", "trilhões"),
    "mil": ("mil", "mil"),
}
NUM = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"


def _to_number(s: str) -> float | int:
    s = s.replace(".", "").replace(",", ".")
    return float(s) if "." in s else int(s)


def number_words(s: str, feminine: bool = False) -> str:
    """'1,5' -> 'um vírgula cinco'; '2.026' -> 'dois mil e vinte e seis'."""
    s = s.replace(".", "")
    if "," in s:
        inteiro, dec = s.split(",", 1)
        dec_words = (
            " ".join(num2words(int(d), lang=LANG) for d in dec)
            if dec.startswith("0")
            else num2words(int(dec), lang=LANG)
        )
        return f"{number_words(inteiro, feminine)} vírgula {dec_words}"
    words = num2words(int(s), lang=LANG)
    if feminine:
        words = re.sub(r"\bum\b", "uma", words)
        words = re.sub(r"\bdois\b", "duas", words)
        words = re.sub(r"entos\b", "entas", words)
    return words


def _money(m: re.Match[str]) -> str:
    value, mult = m.group(1), (m.group(2) or "").lower()
    if mult:
        n = _to_number(value)
        singular, plural = MULTIPLIERS[mult]
        unit = singular if n < 2 else plural
        if mult == "mil":
            return f"{number_words(value, feminine=False)} mil reais"
        return f"{number_words(value)} {unit} de reais"
    n = _to_number(value)
    if isinstance(n, float):
        reais, cent = value.replace(".", "").split(",")
        cent = cent.ljust(2, "0")[:2]
        txt = f"{number_words(reais)} {'real' if int(reais) == 1 else 'reais'}"
        if int(cent):
            txt += f" e {number_words(cent)} centavos"
        return txt
    return f"{number_words(value)} {'real' if n == 1 else 'reais'}"


def _ordinal(m: re.Match[str]) -> str:
    words = num2words(int(m.group(1)), lang=LANG, to="ordinal")
    if m.group(2) in ("ª", "a"):
        words = re.sub(r"o\b", "a", words)
    return words


def _hour(m: re.Match[str]) -> str:
    h, mins = int(m.group(1)), m.group(2)
    txt = number_words(str(h), feminine=True) + (" hora" if h == 1 else " horas")
    if mins and int(mins):
        txt = f"{number_words(str(h), feminine=True)} e {number_words(mins.lstrip('0') or '0')}"
    return txt


def normalize_numbers(text: str) -> str:
    # dinheiro: R$ 1,5 mi / R$ 300 mil / R$ 25,90
    text = re.sub(
        rf"R\$\s?({NUM})(?:\s?(mi|milhão|milhões|bi|bilhão|bilhões|tri|trilhão|trilhões|mil)\b)?",
        _money,
        text,
        flags=re.I,
    )
    # placar: 2x1, 2 x 1
    text = re.sub(
        r"\b(\d{1,2})\s?[xX×]\s?(\d{1,2})\b",
        lambda m: f"{number_words(m.group(1))} a {number_words(m.group(2))}",
        text,
    )
    # porcentagem: 15%, 1,5%
    text = re.sub(rf"({NUM})\s?%", lambda m: f"{number_words(m.group(1))} por cento", text)
    # horário: 18h, 18h30
    text = re.sub(r"\b(\d{1,2})h(\d{2})?\b", _hour, text)
    # ordinal: 5º, 2ª
    text = re.sub(r"\b(\d{1,3})\s?([ºª°])", _ordinal, text)
    # números restantes
    text = re.sub(rf"\b({NUM})\b", lambda m: number_words(m.group(1)), text)
    return text


@lru_cache
def load_pronunciation(path: Path | None = None) -> tuple[dict[str, str], dict[str, str]]:
    path = path or get_settings().config_dir / "pronuncia.yaml"
    if not path.exists():
        return {}, {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("siglas") or {}, data.get("nomes") or {}


def apply_dictionary(text: str, siglas: dict[str, str], nomes: dict[str, str]) -> str:
    for sigla, spoken in siglas.items():  # siglas: só em maiúsculas exatas
        text = re.sub(rf"(?<![\w-]){re.escape(sigla)}(?![\w-])", spoken, text)
    for nome, spoken in nomes.items():  # nomes: sem diferenciar maiúsculas
        text = re.sub(rf"(?<!\w){re.escape(nome)}(?!\w)", spoken, text, flags=re.I)
    return text


def normalize_text(text: str) -> str:
    siglas, nomes = load_pronunciation()
    text = apply_dictionary(text, siglas, nomes)
    text = normalize_numbers(text)
    text = text.replace("&", " e ").replace("/", " ")
    return re.sub(r"\s+", " ", text).strip()
