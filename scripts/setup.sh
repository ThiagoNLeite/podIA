#!/usr/bin/env bash
# podIA — setup no Linux/macOS. Uso: chmod +x scripts/setup.sh && ./scripts/setup.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"

# 1. .env
if [ ! -f "$BACKEND/.env" ]; then
  cp "$ROOT/.env.example" "$BACKEND/.env"
  echo "Criado backend/.env a partir do .env.example"
fi
grep -qE "^GEMINI_API_KEY=\S+" "$BACKEND/.env" \
  || echo "⚠️  GEMINI_API_KEY vazia em backend/.env — sem ela, só o gerador local (sem IA) funciona."

# 2. Ferramentas do sistema
for tool in ffmpeg espeak-ng; do
  command -v "$tool" >/dev/null || echo "⚠️  $tool não encontrado (apt install $tool / brew install $tool)"
done

# 3. Backend (Python 3.12)
PY="${PYTHON:-python3.12}"
[ -d "$BACKEND/.venv" ] || "$PY" -m venv "$BACKEND/.venv"
"$BACKEND/.venv/bin/pip" install -q --upgrade pip
"$BACKEND/.venv/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cpu
"$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"

# 4. App
if [ -f "$ROOT/mobile/package.json" ]; then (cd "$ROOT/mobile" && npm install); fi

# 5. Testes
(cd "$BACKEND" && .venv/bin/python -m pytest -q)
echo "Pronto! Backend: docker compose up --build"
