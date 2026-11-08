# Pendências — ajustes a levar para o README

Lista viva: tudo que a implementação mostrou que o README precisa mudar. Ao aplicar no README, marque com [x].

## Descobertas da Fase 0 (08/11/2026)
- [ ] §11.1 / §13.2: Python **3.12** (Kokoro não instala no 3.13+). Comando: `py -3.12 -m venv .venv`.
- [ ] §10 / §4.4: `GEMINI_MODEL=gemini-flash-lite-latest` **não existe** → usar `gemini-3.5-flash-lite`. Explicar como listar modelos disponíveis.
- [ ] §4.1: mínimo de palavras da matéria **150 → 250** (com menos, o diálogo de 2 min vira enchimento).
- [ ] §4.1: descartar domínios **`.pt`** (Google News pt-BR mistura sites de Portugal).
- [ ] §4.1: nova checagem — texto extraído precisa "bater" com o título (às vezes o trafilatura pega outro artigo da página).
- [ ] §4.1: resumo (`summary`) do Google News é só HTML com links; não serve para o gerador local → ele usa o texto extraído.
- [ ] §2.1 / §4.4: o diálogo agora tem **exatamente 11 falas** (Dora abre e fecha), com meta de palavras por fala. Atualizar o desenho do episódio.
- [ ] §4.4: validação extra — rejeitar diálogo **sem acentos** (o modelo às vezes devolve "nao", "materia"...).
- [ ] §4.4: erros temporários do LLM (429/503) ganham nova chamada com espera (5 s, 15 s) antes de trocar de provedor.
- [ ] §4.4: Groq e Ollama ficaram juntos em `dialogue/openai_compat.py` (README cita `groq.py`).
- [ ] §4.6: montagem feita com numpy + ffmpeg direto (pydub não é usado). Remover pydub das dependências citadas.
- [ ] §2 / §4.5: decisão da Fase 0 — **Kokoro aprovado** (usuário gostou das vozes). Piper fica só como plano B documentado, sem implementação.
- [ ] §14 Fase 0: anotar tempos medidos — ~50 s por episódio em CPU (16 núcleos); carregar o modelo ~8 s (1ª vez ~50 s, baixa ~330 MB).
- [ ] §11.1: no Windows, ffmpeg e espeak-ng via `winget install Gyan.FFmpeg` e `winget install eSpeak-NG.eSpeak-NG`.

## Decisões da Fase 2 (08/11/2026)
- [ ] §5.1: `POST /admin/generate` usa `force=True` = pode **reaproveitar a notícia mais recente** (gera de novo mesmo sem notícia nova). Documentar.
- [ ] §5.3/§5.4: semântica do `503` — se a última geração falhou e não há episódio, o `GET /episodes/latest` devolve `503` **uma vez**; a próxima chamada ("Tentar de novo") dispara nova geração e volta `202`.
- [ ] §5.1: campos reais do `/health`: `status`, `motor_voz`, `motor_voz_carregado`, `llm_configurado`, `gerando` (lista de temas), `ultimo_ciclo` (inicio, fim, resultados por tema).
- [ ] §5.4: erro de parâmetro faltando/ inválido devolve `422` com `{erro: "parametro_invalido", ...}` (não estava na tabela).
- [ ] §6: `episodio` só é gravado depois que a notícia é escolhida (`noticia_id` é NOT NULL). Falhas antes disso (sem internet, RSS fora) ficam só em memória/log.
- [ ] §6: datas gravadas em **UTC com fuso**; a API converte para `TZ`. No Windows precisa do pacote `tzdata` (já no requirements).
- [ ] §10: nova variável `SCHEDULER_ENABLED` (padrão `true`; os testes usam `false`).
- [ ] §3.2/§11.3: Docker usa **PyTorch só-CPU** (a versão padrão do Linux traz CUDA, > 2 GB). Volume nomeado `podia-data` guarda banco, áudios e o cache do modelo (`HF_HOME`).
- [ ] §4.6: `loudnorm` derruba o ffmpeg com silêncio absoluto → o código pula a normalização quando não há sinal.
- [ ] §4.4: se todas as tentativas falharem **só pelo tamanho**, aceita a mais longa com ≥ 220 palavras (antes caía no gerador local, que gera ~50 s). Na prática os episódios ficam com ~1:37–1:45.
- [ ] §2.1 / prompt: Dora (falas 3, 5, 7, 9) com 40–50 palavras; perguntas do Alex curtas (8–15 palavras). ✅ feito no prompt.
- [ ] §11.2: `scripts/setup.sh` e `scripts/setup.ps1` criados (instalam torch só-CPU antes do requirements). Conferir texto do README.
- [ ] §9: arquivos novos — `backend/requirements.txt`, `backend/.dockerignore`, `PENDENCIAS.md`; `scripts/spike_gnews.py` (teste da Fase 0).

## Decisões da Fase 3 (08/11/2026)
- [ ] §7.1 / §11.4: **sem Expo Go** — desenvolvimento com *development build* (`npx expo run:android`) no emulador do Android Studio; teste real no celular via USB. Motivo: áudio em segundo plano + controles na tela de bloqueio exigem build nativo (config plugin do expo-audio).
- [ ] §11.4: conexão com o backend — emulador usa `http://10.0.2.2:8000`; celular via USB usa `adb reverse tcp:8000 tcp:8000` + `http://localhost:8000`; Wi-Fi usa `http://IP-do-PC:8000` (liberar firewall). Padrão do app: `10.0.2.2` (ou `EXPO_PUBLIC_API_URL`).
- [ ] §11.1: requisitos do app mudam — Android Studio (SDK + emulador) em vez de Expo Go; `JAVA_HOME` apontando para o JBR do Android Studio (Java 17+; o Java 8 do sistema não serve).
- [ ] §11.5: Windows — **não usar `subst`** para encurtar o caminho: o Node resolve para o caminho real e o codegen do React Native falha ("different roots"). Resultado do build no caminho do OneDrive: (preencher). Recomendação a avaliar: manter o repositório fora do OneDrive (ex.: `C:\dev\podIA`) — caminho curto e sem sincronizar node_modules/.venv/build (vários GB).
- [ ] §7.1: Expo **SDK 58**; código em `mobile/src/` (o README fala em `mobile/app/`, `mobile/components/`...). Estrutura real: `src/app` (rotas), `src/components`, `src/hooks/use-api.ts`, `src/services` (api, settings, format), `src/theme/colors.ts`, `src/types/api.ts`.
- [ ] §8: efeito *glass* feito com fundo translúcido + borda sobre gradiente (sem `expo-blur`: no Android o blur exige `BlurTargetView` e é pesado; visualmente o resultado é o mesmo sobre o gradiente).
- [ ] §8: fonte do sistema (sem Inter) e ícones Ionicons. Ícone do app reaproveitado do PodAI (microfone de vidro roxo + ondas amarelas).
- [ ] §7.2: extras implementados — tocar numa fala da transcrição pula o áudio para ela; o player começa a tocar sozinho; barra de progresso tocável.
- [ ] §7.2: sair da tela do Player para o áudio (segundo plano = app minimizado / tela bloqueada).

## Melhorias de qualidade a fazer (não é README)
- [x] Prompt: perguntas do Alex estão longas demais ("enchimento"); deixá-las curtas e alongar as respostas da Dora.
- [ ] Gemini quase sempre erra o tamanho na 1ª tentativa (2–3 chamadas por episódio). Ainda dentro da cota grátis, mas vale melhorar.
- [ ] Vinheta `assets/vinheta.mp3` (livre de direitos) — ainda não existe; o código funciona sem ela.
