# podIA — instruções para o Claude Code

- A especificação completa está no README.md. Siga-a; se algo for ambíguo, pergunte antes de inventar.
- Implemente apenas a fase pedida. Não adiante funcionalidades de fases futuras.
- Backend: Python 3.12 (Kokoro não suporta 3.13+), FastAPI, SQLModel, type hints em tudo, ruff para lint/format.
- App: Expo + TypeScript estrito, Expo Router, TanStack Query.
- Código e nomes técnicos em inglês; textos mostrados ao usuário, prompts e comentários de domínio em português.
- Toda etapa do pipeline é uma função testável; testes não acessam a internet (use tests/fixtures).
- Nunca coloque chaves de API no código; leia de settings.py (backend/.env).
- Ao terminar uma tarefa: rode `pytest -q` e `ruff check .` (em backend/) e corrija o que falhar.
- Comandos: `docker compose up --build` · `cd backend && .venv/Scripts/python -m pytest -q` · `cd mobile && npx expo start`
- Windows: ffmpeg e espeak-ng instalados via winget. venv em backend/.venv (criado com `py -3.12`).
