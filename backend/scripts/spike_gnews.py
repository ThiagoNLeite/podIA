"""Fase 0 — teste do risco nº 1: resolver links do Google News RSS e extrair o texto.

Uso: python scripts/spike_gnews.py [termos de busca] [--n 5]
"""

from __future__ import annotations

import argparse
import time
import urllib.parse

import feedparser
import httpx
import trafilatura
from googlenewsdecoder import gnewsdecoder

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("busca", nargs="?", default='futebol OR brasileirão OR libertadores')
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()

    q = urllib.parse.quote(f"{args.busca} when:1d")
    rss = f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    feed = feedparser.parse(rss, agent=UA)
    print(f"RSS: {len(feed.entries)} itens\n")

    ok_decode = ok_extract = 0
    for e in feed.entries[: args.n]:
        print(f"• {e.title}\n  publicado: {e.get('published')}")
        t0 = time.time()
        res = gnewsdecoder(e.link, interval=1)
        if not res.get("success"):
            print(f"  ✗ decode falhou: {res.get('message')}\n")
            continue
        url = res["decoded_url"]
        ok_decode += 1
        print(f"  ✓ URL real ({time.time() - t0:.1f}s): {url}")
        try:
            html = httpx.get(url, headers={"User-Agent": UA}, timeout=10, follow_redirects=True).text
            text = trafilatura.extract(html) or ""
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ download falhou: {exc}\n")
            continue
        words = len(text.split())
        if words >= 150:
            ok_extract += 1
        print(f"  {'✓' if words >= 150 else '✗'} texto extraído: {words} palavras")
        print(f"    \"{text[:160].replace(chr(10), ' ')}...\"\n")

    n = min(args.n, len(feed.entries))
    print(f"RESUMO: decode {ok_decode}/{n} · extração ≥150 palavras {ok_extract}/{n}")


if __name__ == "__main__":
    main()
