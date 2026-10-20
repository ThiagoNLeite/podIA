# podIA
Aplicativo que gera podcast
# 🎧 podIA — Notícia em 2 minutos

> Aplicativo Android que transforma a notícia mais recente de um tema em um mini-podcast de ~2 minutos, em formato de **diálogo entre dois apresentadores**, gerado por IA. Projeto acadêmico, **simples, funcional e com custo zero**.

**Status:** Planejamento
**Versão do documento:** 0.3 — 19/10/2026
**Responsável:** Thiago Nascimento Leite
**Contexto:** Trabalho de faculdade

---

## 1. Visão geral

### 1.1 Nome
**podIA** = *pod*cast + *IA*. Tagline: *"Seu podcast de notícias, feito por IA, em 2 minutos."*

### 1.2 O que o app faz
1. O usuário abre o app e vê 6 temas.
2. Toca em um tema (ex.: **Futebol**).
3. Ouve um episódio de ~2 minutos em que **dois apresentadores conversam** sobre a notícia mais recente daquele tema.
4. Na tela aparece o título da notícia e o link da fonte original.

### 1.3 Temas do MVP
⚽ Futebol · 🎌 Anime · 🎬 Filmes · 🏛️ Política · 💻 Tecnologia · 🚗 Automotivo

### 1.4 Escopo do MVP (decisões fechadas)
| Decisão | Escolha |
|---|---|
| Plataforma | **Somente Android** (APK) |
| Backend | **API própria** (FastAPI) |
| Banco de dados | **SQLite** (arquivo único, sem servidor) |
| Conteúdo do episódio | **1 notícia por tema** — a mais recente válida |
| Formato do áudio | **Diálogo com duas vozes** |
| Voz | Modelo aberto (Kokoro) rodando no próprio backend, sem API paga |
| Custo | **R$ 0** |

### 1.5 Fora do escopo do MVP
iOS, login, favoritos, histórico, notificações, download offline, voz personalizada, publicação na Play Store.

---

## 2. Os apresentadores

Dois personagens fixos dão identidade ao podIA:

| Personagem | Papel | Voz (Kokoro) |
|---|---|---|
| **Dora** | Âncora: apresenta a notícia, traz os fatos | `pf_dora` (feminina, pt-BR) |
| **Alex** | Comentarista: faz perguntas, resume e explica o "por que isso importa" | `pm_alex` (masculina, pt-BR) |

**Estrutura de um episódio (~2 min, ~300 palavras, 8–12 falas):**
```
DORA: Abertura — "Oi, eu sou a Dora..."    ALEX: "...e eu sou o Alex. Hoje no podIA Futebol..."
DORA: O fato principal (o quê, quem, quando)
ALEX: Pergunta ou reação ("E o que isso muda na tabela?")
DORA: Detalhes e contexto
ALEX: Resumo — por que isso importa
DORA: Fechamento — "A fonte completa está no app. Até a próxima!"
```

Regras do diálogo:
- Conversa natural, mas **somente com informações da matéria**. Alex não opina sobre pessoas nem inventa fatos.
- Em **Política**, os dois mantêm tom neutro e informativo.
- Frases curtas, escritas para serem ouvidas.

---

## 3. Arquitetura

```
┌─────────────────────┐        HTTP (JSON + MP3)        ┌──────────────────────────────────────┐
│   App podIA          │ ─────────────────────────────▶ │          Backend podIA (Docker)       │
│   React Native/Expo  │ ◀───────────────────────────── │                                      │
│   - 6 temas          │                                │  FastAPI ── rotas /themes /episodes   │
│   - player           │                                │     │                                │
└─────────────────────┘                                │  APScheduler (a cada 3h)              │
                                                        │     │                                │
                                                        │  Pipeline:                            │
                                                        │   1. Busca notícia (RSS)              │
                                                        │   2. Extrai texto (trafilatura)       │
                                                        │   3. Gera diálogo (Gemini Flash grátis)│
                                                        │   4. Gera vozes (Kokoro, local)       │
                                                        │   5. Monta MP3 (ffmpeg)               │
                                                        │     │                                │
                                                        │  SQLite (podia.db) + pasta /audio     │
                                                        └──────────────────────────────────────┘
```

### 3.1 Como funciona
- **A cada 3 horas**, o agendador roda o pipeline para os 6 temas e salva um episódio novo de cada (só se houver notícia nova).
- Quando o usuário toca num tema, a API devolve **o último episódio já pronto** → o áudio começa na hora.
- Se não existir episódio do tema (ex.: primeiro uso), a API gera na hora e o app mostra "Preparando seu podIA…".

### 3.2 Onde o backend roda (custo zero)
| Opção | Quando usar | Observação |
|---|---|---|
| **Notebook/PC do desenvolvedor** ⭐ | Desenvolvimento e apresentação | Celular acessa pela mesma rede Wi-Fi, ou por túnel gratuito (Cloudflare Tunnel / ngrok) |
| Oracle Cloud "Always Free" (VM ARM) | Se quiser deixar online 24h | Tem memória suficiente para o Kokoro; exige cadastro com cartão (não cobra no plano grátis) |

> ⚠️ Hospedagens gratuitas comuns (Render, Koyeb etc.) têm pouca memória (~512 MB) para rodar um modelo de voz e "dormem" sem uso — o agendador não dispara. Por isso não são recomendadas para este projeto.

Tudo em **um único container Docker**, para rodar igual em qualquer máquina:
```bash
docker compose up
```

---

## 4. Pipeline

### 4.1 Busca da notícia (RSS)
Fonte principal: **Google News RSS**, edição Brasil, com busca por tema:
```
https://news.google.com/rss/search?q=<termos>+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419
```
Fontes extras: RSS direto de portais do tema (lista em `themes.yaml`).

**Regra de seleção (simples):**
1. Pegar os itens das últimas **24h** (se não houver, ampliar para **72h**).
2. Ordenar do mais recente para o mais antigo.
3. Escolher o **primeiro item válido**:
   - não contém palavras bloqueadas (ex.: "apostas", "palpite", "bet");
   - o texto da matéria foi extraído com pelo menos **150 palavras** (se não, passa para o próximo);
   - ainda não foi usado em um episódio anterior (checa a URL no banco).

> 💡 Ajuste fácil para depois: preferir a mais recente **entre as que aparecem em 2+ veículos**, para evitar notícias muito pequenas. Fica como melhoria, não entra no MVP.

### 4.2 Extração do texto
- Resolver o link do Google News para a URL real do portal.
- `trafilatura` extrai só o corpo da matéria.
- O texto **não é reproduzido**: serve apenas de base para o diálogo, e o link da fonte aparece no app.

### 4.3 Configuração dos temas (`config/themes.yaml`)
```yaml
futebol:
  nome: Futebol
  icone: ⚽
  busca: "futebol OR brasileirão OR libertadores OR seleção brasileira"
  feeds_extras: []
  bloqueadas: ["apostas", "palpite", "bet", "odds"]

anime:
  nome: Anime
  icone: 🎌
  busca: "anime OR mangá OR crunchyroll"
  janela_horas: 72          # tema com menos notícias
  bloqueadas: []

politica:
  nome: Política
  icone: 🏛️
  busca: "política Brasil OR Congresso OR STF OR Planalto"
  tom: neutro
  bloqueadas: []
# filmes, tecnologia, automotivo...
```

### 4.4 Geração do diálogo (LLM gratuito)
- **Principal:** Gemini Flash / Flash-Lite pelo **plano gratuito** do Google AI Studio. São no máximo 6 chamadas a cada 3h (48/dia), muito abaixo dos limites diários.
- **Plano B:** outro provedor com plano grátis (ex.: Groq) ou modelo local via Ollama, acionado se a API retornar erro de limite (429).
- Observação: no plano grátis do Gemini os dados podem ser usados para treinar o modelo — sem problema, pois são notícias públicas.

Saída exigida do modelo (JSON):
```json
{
  "titulo_episodio": "Time X vence clássico e assume a liderança",
  "falas": [
    { "voz": "dora", "texto": "Oi, eu sou a Dora!" },
    { "voz": "alex", "texto": "E eu sou o Alex. Hoje no podIA Futebol..." }
  ]
}
```
Validações no código: JSON válido, só vozes `dora`/`alex`, total entre 260 e 330 palavras. Se falhar, tenta de novo (máx. 2 vezes).

O prompt fica em `prompts/dialogo.md` (versionado, fácil de ajustar).

### 4.5 Geração das vozes (Kokoro — nosso gerador de voz)
- **Kokoro-82M**: modelo aberto, licença Apache 2.0, roda em CPU, vozes pt-BR `pf_dora` e `pm_alex`.
- Empacotado dentro do backend como o módulo **`podia_tts`** — nenhuma API externa, nenhum custo.
- Para cada fala: **normalizar o texto** → sintetizar com a voz do personagem.

Normalização (o que mais melhora a qualidade):
- números por extenso ("2x1" → "dois a um");
- siglas soletradas ou expandidas ("STF" → "S T F");
- dicionário de pronúncia para nomes estrangeiros (`config/pronuncia.yaml`).

> Plano B de voz: **Piper** (`pt_BR-faber-medium`), mais leve e estável, caso o Kokoro fique lento ou soe mal em algum tema. A interface do `podia_tts` permite trocar de motor sem mudar o resto.

### 4.6 Montagem do áudio (ffmpeg / pydub)
1. Juntar as falas na ordem, com **pausa de ~0,3 s** entre elas.
2. Vinheta curta de abertura e encerramento (2–3 s, livre de direitos).
3. Normalizar volume (–16 LUFS).
4. Exportar **MP3 64 kbps** (~1 MB).
5. Conferir duração (1:40 a 2:30).

**Limpeza:** manter só os últimos 7 dias de áudios (~170 MB no máximo).

---

## 5. API

| Método | Rota | Retorno |
|---|---|---|
| `GET` | `/themes` | Lista dos 6 temas + horário do último episódio de cada |
| `GET` | `/episodes/latest?theme=futebol` | Último episódio do tema (gera na hora se não existir) |
| `GET` | `/episodes/{id}` | Episódio específico |
| `GET` | `/audio/{arquivo}.mp3` | Arquivo de áudio (streaming) |
| `POST` | `/admin/generate?theme=futebol` | Força a geração de um novo episódio (protegido por chave) |
| `GET` | `/health` | Status da API |

Exemplo de resposta de `/episodes/latest?theme=futebol`:
```json
{
  "id": 42,
  "tema": "futebol",
  "titulo": "Time X vence clássico e assume a liderança",
  "gerado_em": "2026-10-19T18:04:12-04:00",
  "duracao_s": 118,
  "audio_url": "/audio/futebol_42.mp3",
  "fonte": { "veiculo": "ge", "url": "https://..." },
  "aviso": "Episódio gerado por IA a partir da fonte indicada."
}
```

A documentação interativa sai automaticamente em `/docs` (Swagger do FastAPI) — útil para a apresentação.

---

## 6. Banco de dados (SQLite)

Duas tabelas — o mínimo necessário:

```sql
CREATE TABLE noticia (
  id            INTEGER PRIMARY KEY,
  tema          TEXT NOT NULL,
  titulo        TEXT NOT NULL,
  url           TEXT NOT NULL UNIQUE,   -- evita repetir notícia
  veiculo       TEXT,
  publicada_em  DATETIME,
  texto         TEXT,
  coletada_em   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE episodio (
  id            INTEGER PRIMARY KEY,
  tema          TEXT NOT NULL,
  noticia_id    INTEGER NOT NULL REFERENCES noticia(id),
  titulo        TEXT NOT NULL,
  dialogo_json  TEXT NOT NULL,          -- falas geradas (auditoria)
  audio_arquivo TEXT NOT NULL,
  duracao_s     INTEGER,
  status        TEXT DEFAULT 'pronto',  -- pronto | erro
  gerado_em     DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Acesso com **SQLModel** ou **SQLAlchemy**. Os temas ficam no `themes.yaml`, não no banco (mais simples de editar).

---

## 7. Aplicativo Android

### 7.1 Tecnologia
- **React Native + Expo (TypeScript)** — gratuito.
- Player: `expo-audio` (com reprodução em segundo plano).
- APK gerado com **EAS Build** (plano grátis) ou build local.
- URL da API configurável (`.env`), para trocar entre notebook e servidor.

### 7.2 Telas
**Home**
- Logo podIA.
- Grade 2×3 com os 6 temas (como no esboço).
- Embaixo de cada tema: "atualizado às 18h".

**Player**
- Nome do tema + título da notícia.
- Indicação de quem está falando? → **não no MVP** (manter simples).
- Play/pause, barra de progresso, velocidade 1x / 1.25x / 1.5x.
- Card da fonte com botão "Ler matéria completa".
- Aviso "Gerado por IA".

**Estados**
- "Preparando seu podIA…" (quando gera na hora)
- Sem internet / servidor indisponível
- Erro ao gerar → botão "Tentar de novo"

---

## 8. Estrutura do repositório
```
podia/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI
│   │   ├── routes.py
│   │   ├── db.py              # SQLite
│   │   ├── models.py
│   │   ├── scheduler.py       # APScheduler (3h)
│   │   └── pipeline/
│   │       ├── news.py        # RSS + seleção
│   │       ├── extract.py     # trafilatura
│   │       ├── dialogue.py    # Gemini → JSON de falas
│   │       ├── podia_tts/     # gerador de voz
│   │       │   ├── base.py
│   │       │   ├── normalize.py
│   │       │   ├── kokoro_engine.py
│   │       │   └── piper_engine.py
│   │       └── audio.py       # montagem do MP3
│   ├── config/
│   │   ├── themes.yaml
│   │   └── pronuncia.yaml
│   ├── prompts/dialogo.md
│   ├── assets/vinheta.mp3
│   ├── data/                  # podia.db + audio/ (fora do git)
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── mobile/                    # app Expo
│   ├── app/                   # telas (home, player)
│   ├── components/
│   └── services/api.ts
├── docker-compose.yml
├── .env.example               # GEMINI_API_KEY, ADMIN_KEY
└── README.md
```

---

## 9. Roadmap

### Fase 0 — Prova de conceito (1 semana)
Objetivo: um MP3 bom de um tema, sem API e sem app.
- [ ] Script único: Futebol → notícia mais recente → texto → diálogo (Gemini) → vozes (Kokoro) → `futebol.mp3`
- [ ] Testar o Kokoro em pt-BR com as duas vozes; comparar com Piper como plano B
- [ ] Ajustar o prompt até o diálogo soar natural
- [ ] Normalização básica (números e siglas)
- [ ] Medir tempo de geração de um episódio no notebook
- **Entrega:** 1 episódio de Futebol que você ouviria de verdade.

### Fase 1 — Pipeline para os 6 temas (1 semana)
- [ ] `themes.yaml` com os 6 temas
- [ ] Regra de seleção (recente, válida, não repetida)
- [ ] Validação do JSON do diálogo + nova tentativa
- [ ] Montagem com vinheta e normalização de volume
- [ ] Testar um episódio de cada tema e ajustar buscas/bloqueios
- **Entrega:** 6 episódios gerados por um comando.

### Fase 2 — Backend (1–2 semanas)
- [ ] FastAPI com as rotas do §5
- [ ] SQLite com as tabelas do §6
- [ ] Agendador a cada 3h
- [ ] Geração na hora quando não houver episódio
- [ ] Limpeza de áudios com mais de 7 dias
- [ ] Docker + docker-compose
- [ ] Logs simples de erro por etapa
- **Entrega:** `docker compose up` e a API serve episódios atualizados sozinha.

### Fase 3 — App Android (2 semanas)
- [ ] Projeto Expo + identidade visual podIA
- [ ] Tela Home com os 6 temas
- [ ] Tela Player com áudio em segundo plano
- [ ] Card da fonte
- [ ] Estados de carregamento e erro
- [ ] Gerar APK
- **Entrega:** APK instalado no celular tocando episódios do backend.

### Fase 4 — Testes e ajustes (1 semana)
- [ ] Teste com 5–10 colegas (nota da voz, clareza, erros)
- [ ] Revisar episódios de Política (neutralidade)
- [ ] Corrigir pronúncias recorrentes no `pronuncia.yaml`
- [ ] Testes automatizados básicos (seleção de notícia, validação do JSON, rotas da API)
- **Entrega:** versão estável para apresentar.

### Fase 5 — Entrega acadêmica (1 semana)
- [ ] README com instruções de instalação
- [ ] Documento de arquitetura e decisões (este MD como base)
- [ ] Roteiro da demonstração ao vivo (deixar episódios já gerados antes da apresentação)
- [ ] Limitações e trabalhos futuros

**Prazo total estimado:** 7–8 semanas.

---

## 10. Riscos e como lidar
| Risco | Mitigação |
|---|---|
| IA inventar informações | Prompt restrito ao texto da matéria; temperatura baixa; diálogo salvo no banco para conferência |
| Voz pt-BR do Kokoro soar artificial | Normalização de texto + dicionário de pronúncia; Piper como plano B |
| Notícia "mais recente" ser fraca ou curta | Mínimo de 150 palavras extraídas; senão, pega a próxima |
| Política com viés | Tom neutro obrigatório no prompt; revisão manual na Fase 4 |
| Limite do Gemini grátis atingido | Nova tentativa com espera + provedor gratuito alternativo |
| Google News mudar o formato do RSS | Feeds diretos de portais como reserva no `themes.yaml` |
| Site bloquear a extração | Usar título + resumo do RSS ou passar para a próxima notícia |
| Notebook desligado na hora da demo | Gerar episódios antes e testar a conexão do celular com antecedência |
| Direitos autorais | Texto original nunca é lido no áudio; fonte e link sempre visíveis |

---

## 11. Melhorias futuras (pós-trabalho)
1. Preferir notícias cobertas por 2+ veículos
2. Giro com 2–3 notícias por episódio
3. Mais temas
4. Mostrar no player quem está falando (Dora/Alex)
5. Favoritos e histórico
6. Download offline
7. Notificação de episódio novo
8. Hospedagem 24h (Oracle Always Free)

---

## 12. Próximo passo
**Fase 0:** script de prova de conceito de Futebol, de ponta a ponta, com o diálogo entre Dora e Alex.
