# 🎧 podIA — Notícia em 2 minutos

# Nomes: Heitor Santos Cortes, Thiago Leite e Felipe Shinkae

> Aplicativo Android que transforma a notícia mais recente de um tema em um mini-podcast de ~2 minutos, em formato de **diálogo entre dois apresentadores**, gerado por IA. Projeto acadêmico: **simples, funcional e com custo zero**.

| | |
|---|---|
| **Status** | Planejamento → implementação |
| **Versão do documento** | 1.0 — 08/11/2026 |
| **Responsáveis** | Thiago Leite, Felipe Shinkai, Heitor |
| **Contexto** | Trabalho de faculdade |
| **Tagline** | *"Seu podcast de notícias, feito por IA, em 2 minutos."* |

Este README é ao mesmo tempo a **especificação do projeto** e o **guia de implementação**. A seção [13. Guia para implementação com Claude Code](#13-guia-para-implementação-com-claude-code) explica como usá-lo para gerar o código fase a fase.

---

## Sumário
1. [Visão geral](#1-visão-geral)
2. [Os apresentadores](#2-os-apresentadores)
3. [Arquitetura](#3-arquitetura)
4. [Pipeline de geração](#4-pipeline-de-geração)
5. [API](#5-api)
6. [Banco de dados](#6-banco-de-dados-sqlite)
7. [Aplicativo Android](#7-aplicativo-android)
8. [Identidade visual](#8-identidade-visual)
9. [Estrutura do repositório](#9-estrutura-do-repositório)
10. [Configuração e variáveis de ambiente](#10-configuração-e-variáveis-de-ambiente)
11. [Instalação e execução](#11-instalação-e-execução)
12. [Testes](#12-testes)
13. [Guia para implementação com Claude Code](#13-guia-para-implementação-com-claude-code)
14. [Roadmap](#14-roadmap)
15. [Riscos e mitigação](#15-riscos-e-mitigação)
16. [Limitações conhecidas](#16-limitações-conhecidas)
17. [Melhorias futuras](#17-melhorias-futuras)

---

## 1. Visão geral

### 1.1 O que o app faz
1. O usuário abre o app e vê 6 temas.
2. Toca em um tema (ex.: **Futebol**).
3. Ouve um episódio de ~2 minutos em que **dois apresentadores conversam** sobre a notícia mais recente daquele tema.
4. Na tela aparecem o título da notícia, a transcrição do diálogo e o link da fonte original.

### 1.2 Temas do MVP
⚽ Futebol · 🎌 Anime · 🎬 Filmes · 🏛️ Política · 💻 Tecnologia · 🚗 Automotivo

Os temas ficam em `config/themes.yaml`. Adicionar um tema novo = adicionar um bloco no YAML, sem mexer em código.

### 1.3 Decisões fechadas
| Decisão | Escolha | Motivo |
|---|---|---|
| Plataforma | **Somente Android** (APK) | Escopo menor; Expo permite iOS depois |
| Backend | **API própria em Python (FastAPI)** | Voz de qualidade precisa de servidor; episódios pré-gerados tocam na hora |
| Banco | **SQLite** (arquivo único) | Zero servidor, zero custo |
| Conteúdo | **1 notícia por tema** — a mais recente válida | Simplicidade |
| Janela de tempo | **24h**, ampliando para **72h** se não houver notícia; **nunca mais de 72h** | Notícia fresca, com garantia de que sempre haja conteúdo |
| Formato | **Diálogo com duas vozes** | É o que diferencia o podIA de um leitor de manchetes |
| Roteiro | LLM gratuito (Gemini) + **gerador local de reserva** (sem IA) | O app nunca fica sem episódio |
| Voz | **Kokoro-82M** local no backend; **Piper** como plano B | Sem API paga |
| App | **React Native + Expo (TypeScript)** | Gratuito, gera APK, um código só |
| Custo | **R$ 0** | Requisito do projeto |

### 1.4 Fora do escopo do MVP
iOS, login, favoritos, histórico, notificações, download offline, voz personalizada, publicação na Play Store, giro com várias notícias por episódio.

---

## 2. Os apresentadores

| Personagem | Papel | Voz (Kokoro) | Voz (Piper, plano B) |
|---|---|---|---|
| **Dora** | Âncora: apresenta a notícia e traz os fatos | `pf_dora` (feminina, pt-BR) | `pt_BR-faber-medium` com pitch ajustado ou outra voz feminina disponível |
| **Alex** | Comentarista: pergunta, resume e explica "por que isso importa" | `pm_alex` (masculina, pt-BR) | `pt_BR-faber-medium` |

### 2.1 Estrutura do episódio (~2 min, ~300 palavras, 8–12 falas)
```
DORA: Abertura         — "Oi, eu sou a Dora..."
ALEX: Apresentação     — "...e eu sou o Alex. Hoje no podIA Futebol..."
DORA: Fato principal   — o quê, quem, quando
ALEX: Pergunta/reação  — "E o que isso muda na tabela?"
DORA: Detalhes e contexto
ALEX: Resumo           — por que isso importa
DORA: Fechamento       — "A matéria completa está no app. Até a próxima!"
```

### 2.2 Regras do diálogo
- Conversa natural, mas **somente com informações presentes na matéria**. Ninguém inventa fatos, números, datas ou declarações.
- Alex **não opina** sobre pessoas, partidos, times ou empresas; ele pergunta e resume.
- Em **Política**, tom obrigatoriamente neutro e informativo; atribuir afirmações a quem as fez ("segundo o ministro…").
- Frases curtas (até ~20 palavras), escritas para serem **ouvidas**: sem parênteses, listas, emojis ou URLs.
- Citar o veículo de origem pelo nome pelo menos uma vez ("segundo o ge…").
- Nunca ler trechos literais longos da matéria (ver §4.2).

---

## 3. Arquitetura

```
┌─────────────────────┐      HTTP (JSON + MP3)      ┌───────────────────────────────────────────┐
│  App podIA          │ ──────────────────────────▶ │          Backend podIA (Docker)            │
│  React Native/Expo  │ ◀────────────────────────── │                                           │
│  - Home (6 temas)   │                             │  FastAPI ── /themes /episodes /audio       │
│  - Player           │                             │     │                                     │
│  - Configurações    │                             │  APScheduler (a cada 3h)                   │
└─────────────────────┘                             │     │                                     │
                                                    │  Pipeline (por tema):                      │
                                                    │   1. news.py      Busca notícia (RSS)      │
                                                    │   2. extract.py   Extrai texto             │
                                                    │   3. dialogue.py  Gera diálogo (LLM)       │
                                                    │        └─ fallback: gerador local          │
                                                    │   4. podia_tts/   Gera vozes (Kokoro)      │
                                                    │   5. audio.py     Monta MP3 (ffmpeg)       │
                                                    │     │                                     │
                                                    │  SQLite (data/podia.db) + data/audio/      │
                                                    └───────────────────────────────────────────┘
```

### 3.1 Fluxo
- **A cada 3 horas**, o agendador roda o pipeline para os 6 temas, **um por vez** (sequencial, para não estourar memória nem limite do LLM). Só cria episódio se houver notícia nova.
- Quando o usuário toca num tema, a API devolve **o último episódio pronto** → o áudio começa na hora.
- Se não existir episódio do tema (ex.: primeiro uso), a API dispara a geração em segundo plano e responde `202` com status `gerando`; o app mostra "Preparando seu podIA…" e consulta de novo a cada 5 s (ver §5.3).
- Um **lock por tema** impede duas gerações simultâneas do mesmo tema (agendador + pedido do usuário ao mesmo tempo).
- Na inicialização do backend, se algum tema não tiver episódio, a geração inicial é disparada automaticamente.

### 3.2 Onde o backend roda (custo zero)
| Opção | Quando usar | Observação |
|---|---|---|
| **Notebook/PC do desenvolvedor** ⭐ | Desenvolvimento e apresentação | Celular na mesma rede Wi-Fi, ou túnel gratuito (Cloudflare Tunnel / ngrok) |
| Oracle Cloud "Always Free" (VM ARM) | Deixar online 24h | Memória suficiente para o Kokoro; exige cadastro com cartão (não cobra no plano grátis) |

> ⚠️ Hospedagens gratuitas comuns (Render, Koyeb etc.) têm ~512 MB de memória — pouco para o modelo de voz — e "dormem" sem uso, então o agendador não dispara. Não recomendadas.

Tudo em **um único container Docker**: `docker compose up`.

---

## 4. Pipeline de geração

Cada etapa é uma função pura e testável, com entrada e saída bem definidas. O orquestrador (`pipeline/run.py`) chama as etapas em ordem, registra logs por etapa e grava o resultado no banco.

```python
# Contrato das etapas (assinaturas de referência)
def fetch_candidates(theme: Theme) -> list[NewsItem]            # news.py
def select_news(theme: Theme, candidates: list[NewsItem]) -> Article | None  # news.py (usa extract)
def extract_article(url: str) -> ExtractedText | None           # extract.py
def generate_dialogue(theme: Theme, article: Article) -> Dialogue  # dialogue.py
def synthesize(dialogue: Dialogue) -> list[Segment]             # podia_tts
def assemble(segments: list[Segment], out_path: Path) -> AudioResult  # audio.py
def run_theme(theme_id: str, force: bool = False) -> Episode | None   # run.py
```

### 4.1 Busca da notícia (RSS)
**Fonte principal:** Google News RSS, edição Brasil:
```
https://news.google.com/rss/search?q=<termos>+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419
```
**Fontes extras:** RSS direto de portais do tema (`feeds_extras` no `themes.yaml`). Usados como reserva e também quando o Google News falhar.

**Regra de seleção:**
1. Buscar com `when:1d`. Se não houver candidato válido, buscar com `when:3d`.
2. **Validar a data localmente** (`pubDate`): descartar qualquer item com mais de 72h. O filtro `when:` do Google não é exato, então essa checagem é obrigatória.
3. Ordenar do mais recente para o mais antigo.
4. Escolher o **primeiro item válido**:
   - título e resumo não contêm palavras bloqueadas do tema (comparação sem acento e sem diferenciar maiúsculas);
   - a URL (já resolvida) ainda não foi usada em episódio anterior;
   - o texto extraído tem pelo menos **150 palavras** — senão, tenta o próximo;
   - no máximo **8 candidatos** testados por rodada, para não demorar.
5. Se nenhum candidato passar, o tema fica sem episódio novo nesta rodada (o anterior continua valendo).

### 4.2 Extração do texto
- **Resolver o link do Google News:** as URLs do RSS vêm codificadas (`news.google.com/rss/articles/CBMi...`) e **não** redirecionam de forma simples. Usar a biblioteca `googlenewsdecoder` (ou equivalente) para obter a URL real do portal. Se falhar, passar para o próximo candidato. ⚠️ **Este é o ponto mais frágil do pipeline — validar no primeiro dia da Fase 0.**
- `trafilatura` extrai só o corpo da matéria (sem menus, anúncios, comentários).
- Requisições com `User-Agent` genérico de navegador, timeout de 10 s, sem seguir para sites que exigem login.
- O texto **nunca é reproduzido** no áudio: serve apenas de base para o diálogo. O link da fonte aparece sempre no app.

### 4.3 Configuração dos temas (`config/themes.yaml`)
```yaml
futebol:
  nome: Futebol
  icone: ⚽
  cor: "#22C55E"
  busca: "futebol OR brasileirão OR libertadores OR \"seleção brasileira\""
  feeds_extras:
    - https://ge.globo.com/rss/ge/futebol/
  bloqueadas: ["apostas", "palpite", "bet", "odds", "cassino"]

anime:
  nome: Anime
  icone: 🎌
  cor: "#EC4899"
  busca: "anime OR mangá OR crunchyroll"
  janela_horas: 72          # tema com menos notícias: já começa em 72h
  feeds_extras: []
  bloqueadas: []

filmes:
  nome: Filmes
  icone: 🎬
  cor: "#F97316"
  busca: "filme OR cinema OR estreia OR bilheteria"
  feeds_extras: []
  bloqueadas: []

politica:
  nome: Política
  icone: 🏛️
  cor: "#3B82F6"
  busca: "política Brasil OR Congresso OR STF OR Planalto"
  tom: neutro
  feeds_extras: []
  bloqueadas: []

tecnologia:
  nome: Tecnologia
  icone: 💻
  cor: "#8B5CF6"
  busca: "tecnologia OR inteligência artificial OR smartphone OR startup"
  feeds_extras: []
  bloqueadas: []

automotivo:
  nome: Automotivo
  icone: 🚗
  cor: "#EF4444"
  busca: "carro OR lançamento automotivo OR montadora OR carro elétrico"
  feeds_extras: []
  bloqueadas: []
```
Campos opcionais: `janela_horas` (padrão 24), `tom` (padrão `informativo`), `feeds_extras`, `bloqueadas`. As URLs de `feeds_extras` devem ser conferidas antes do uso.

### 4.4 Geração do diálogo

**Provedores, em ordem de tentativa:**
1. **Gemini** (plano gratuito do Google AI Studio) via SDK `google-genai`. Modelo configurável por `.env` (`GEMINI_MODEL`), usando a versão Flash/Flash-Lite gratuita vigente. No máximo 6 chamadas a cada 3h (~48/dia), bem abaixo dos limites.
2. **Groq** (plano gratuito) ou **Ollama** local — acionado se o Gemini devolver erro de limite (429), erro de servidor ou JSON inválido após as novas tentativas.
3. **Gerador local (sem IA)** — reserva final, inspirado no PodAI: monta um diálogo-modelo com o título, o veículo e as primeiras frases do resumo do RSS. Episódio mais curto, mas o tema nunca fica sem conteúdo. Marcado no banco com `gerador = 'local'`.

Os provedores implementam a mesma interface (`DialogueProvider.generate(theme, article) -> Dialogue`), escolhidos em cadeia.

**Parâmetros:** temperatura 0.4; resposta forçada em JSON (`response_mime_type: application/json` no Gemini).

**Saída exigida (JSON):**
```json
{
  "titulo_episodio": "Time X vence clássico e assume a liderança",
  "falas": [
    { "voz": "dora", "texto": "Oi, eu sou a Dora!" },
    { "voz": "alex", "texto": "E eu sou o Alex. Hoje no podIA Futebol..." }
  ]
}
```

**Validações no código (Pydantic):**
- JSON válido no esquema acima;
- `voz` só pode ser `dora` ou `alex`; a primeira fala é da Dora;
- entre 8 e 12 falas; total entre **260 e 330 palavras**;
- nenhuma fala com URL, emoji ou marcação Markdown;
- `titulo_episodio` com até 90 caracteres.

Se falhar: nova tentativa com a mensagem de erro anexada ao prompt (máx. **2 novas tentativas**); depois, próximo provedor.

**Prompt:** em `prompts/dialogo.md`, versionado. Variáveis: `{tema}`, `{tom}`, `{veiculo}`, `{titulo}`, `{texto}` (cortado em ~1.500 palavras). O prompt deve conter as regras do §2.2 e um exemplo curto de saída.

### 4.5 Geração das vozes (`podia_tts`)
- **Kokoro-82M** (licença Apache 2.0), roda em CPU. Pacote `kokoro` com `KPipeline(lang_code="p")` (português brasileiro). Requer `espeak-ng` instalado no sistema (incluído no Dockerfile).
- Empacotado como o módulo interno **`podia_tts`** — nenhuma API externa.
- Interface comum para trocar de motor via `.env` (`TTS_ENGINE=kokoro|piper`):
  ```python
  class TTSEngine(Protocol):
      def synthesize(self, text: str, voice: str) -> AudioSegment: ...
  ```
- O modelo é carregado **uma vez** na inicialização e reutilizado.

**Normalização do texto (antes de sintetizar)** — é o que mais melhora a qualidade:
- placares e números por extenso: "2x1" → "dois a um", "R$ 1,5 mi" → "um vírgula cinco milhão de reais", "15%" → "quinze por cento" (biblioteca `num2words`, `lang="pt_BR"`);
- siglas soletradas ou expandidas por dicionário: "STF" → "ésse tê éfe", "CBF" → "cê bê éfe"; siglas pronunciáveis ficam como estão ("FIFA", "NASA");
- dicionário de pronúncia para nomes estrangeiros em `config/pronuncia.yaml`:
  ```yaml
  siglas:
    STF: "ésse tê éfe"
    CBF: "cê bê éfe"
  nomes:
    Crunchyroll: "cránchi rôu"
    Netflix: "nétflics"
  ```

> **Plano B de voz: Piper** (`pt_BR-faber-medium`), mais leve e estável. Decidir na Fase 0 comparando os dois motores com o mesmo diálogo.

### 4.6 Montagem do áudio (`pydub` + `ffmpeg`)
1. Juntar as falas na ordem, com **pausa de ~0,3 s** entre elas.
2. **Registrar o início de cada fala** (em segundos) — usado pela transcrição no app.
3. Vinheta curta de abertura e encerramento (2–3 s, livre de direitos) em `assets/vinheta.mp3`. Se o arquivo não existir, seguir sem vinheta.
4. Normalizar volume para **–16 LUFS** (filtro `loudnorm` do ffmpeg).
5. Exportar **MP3 mono, 64 kbps** (~1 MB).
6. Conferir duração: **1:40 a 2:30**. Fora disso, registrar aviso no log (não bloqueia).

Nome do arquivo: `data/audio/<tema>_<id>.mp3`.

**Limpeza diária:** apagar áudios com mais de **7 dias** (o registro no banco permanece, com `audio_arquivo` marcado como expirado). Pico estimado: ~170 MB.

---

## 5. API

### 5.1 Rotas
| Método | Rota | Retorno |
|---|---|---|
| `GET` | `/themes` | Lista dos 6 temas + horário do último episódio de cada |
| `GET` | `/episodes/latest?theme=futebol` | Último episódio do tema (`200`) ou `202` se estiver gerando |
| `GET` | `/episodes/{id}` | Episódio específico |
| `GET` | `/audio/{arquivo}.mp3` | Arquivo de áudio (com suporte a `Range`, para avançar/voltar) |
| `POST` | `/admin/generate?theme=futebol` | Força a geração de um novo episódio (header `X-Admin-Key`) |
| `GET` | `/health` | Status da API, motor de voz carregado, último ciclo do agendador |

Documentação interativa automática em `/docs` (Swagger) — útil na apresentação.

### 5.2 Exemplos de resposta
`GET /themes`
```json
[
  { "id": "futebol", "nome": "Futebol", "icone": "⚽", "cor": "#22C55E",
    "ultimo_episodio_em": "2026-11-08T09:04:12-04:00" }
]
```

`GET /episodes/latest?theme=futebol` → `200`
```json
{
  "id": 42,
  "tema": "futebol",
  "titulo": "Time X vence clássico e assume a liderança",
  "gerado_em": "2026-11-08T09:04:12-04:00",
  "duracao_s": 118,
  "audio_url": "/audio/futebol_42.mp3",
  "gerador": "gemini",
  "fonte": {
    "veiculo": "ge",
    "titulo_original": "Time X vence clássico...",
    "url": "https://ge.globo.com/...",
    "publicada_em": "2026-11-08T07:30:00-04:00"
  },
  "falas": [
    { "voz": "dora", "texto": "Oi, eu sou a Dora!", "inicio_s": 2.5 },
    { "voz": "alex", "texto": "E eu sou o Alex...", "inicio_s": 4.1 }
  ],
  "aviso": "Episódio gerado por IA a partir da fonte indicada."
}
```

### 5.3 Geração na hora (primeiro uso)
`GET /episodes/latest?theme=anime` sem episódio pronto → `202 Accepted`:
```json
{ "status": "gerando", "tema": "anime", "tentar_novamente_em_s": 5 }
```
O app repete a chamada até receber `200`, ou até 3 minutos (depois mostra erro com "Tentar de novo").

### 5.4 Erros
Formato padrão: `{ "erro": "codigo_curto", "mensagem": "texto legível" }`.
| Código HTTP | Quando |
|---|---|
| `404` | Tema ou episódio inexistente |
| `401` | Chave de admin ausente ou errada |
| `503` | Geração falhou e não há episódio anterior do tema |

### 5.5 Outros
- CORS liberado (app em desenvolvimento).
- Horários em ISO 8601 com fuso `America/Cuiaba` (configurável por `TZ`).

---

## 6. Banco de dados (SQLite)

Acesso com **SQLModel**. Os temas ficam no `themes.yaml`, não no banco.

```sql
CREATE TABLE noticia (
  id            INTEGER PRIMARY KEY,
  tema          TEXT NOT NULL,
  titulo        TEXT NOT NULL,
  url           TEXT NOT NULL UNIQUE,   -- URL real (já resolvida); evita repetir notícia
  veiculo       TEXT,
  publicada_em  DATETIME,
  texto         TEXT,                   -- texto extraído (só para gerar o diálogo)
  coletada_em   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE episodio (
  id            INTEGER PRIMARY KEY,
  tema          TEXT NOT NULL,
  noticia_id    INTEGER NOT NULL REFERENCES noticia(id),
  titulo        TEXT NOT NULL,
  dialogo_json  TEXT NOT NULL,          -- falas + inicio_s (auditoria e transcrição)
  gerador       TEXT NOT NULL,          -- gemini | groq | ollama | local
  motor_voz     TEXT NOT NULL,          -- kokoro | piper
  audio_arquivo TEXT,                   -- NULL quando expirado pela limpeza
  duracao_s     INTEGER,
  status        TEXT DEFAULT 'pronto',  -- gerando | pronto | erro
  erro          TEXT,                   -- etapa e mensagem, se status = erro
  gerado_em     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_episodio_tema_data ON episodio (tema, gerado_em DESC);
```

---

## 7. Aplicativo Android

### 7.1 Tecnologia
- **React Native + Expo (TypeScript)**, com **Expo Router** para navegação.
- Player: `expo-audio`, com reprodução em segundo plano e controles na tela de bloqueio.
- Requisições com `fetch` + **TanStack Query** (cache, nova tentativa e consulta periódica do `202`).
- Preferências salvas com `AsyncStorage` (velocidade, URL do servidor).
- APK gerado com **EAS Build** (plano grátis) ou build local.
- URL da API definida em `EXPO_PUBLIC_API_URL` e editável na tela de Configurações (para trocar entre notebook, túnel e servidor sem gerar outro APK).

### 7.2 Telas

**Home**
- Logo podIA no topo.
- Grade 2×3 com os 6 temas (ícone, nome, cor do tema).
- Embaixo de cada tema: "atualizado às 18h" (ou "sem episódio ainda").
- Puxar para atualizar.
- Ícone de engrenagem → Configurações.

**Player**
- Nome do tema + título do episódio.
- Play/pause, voltar 10 s, barra de progresso com tempo, velocidade **1x / 1.25x / 1.5x**.
- **Transcrição** do diálogo (lista de falas com nome do apresentador). A fala atual fica **destacada** conforme o áudio avança, usando `inicio_s` — ideia trazida do PodAI, com custo baixo porque os tempos já vêm da API.
- Card da fonte: veículo, "publicada há X horas", botão **"Ler matéria completa"** (abre no navegador).
- Selo "Gerado por IA". Se `gerador = local`, mostrar "Resumo automático (sem IA)".

**Configurações**
- URL do servidor + botão "Testar conexão" (chama `/health`).
- Velocidade padrão de reprodução.
- Sobre: versão, aviso de IA, créditos (Kokoro, fontes de notícia).

**Estados**
- "Preparando seu podIA…" (resposta `202`), com animação simples.
- Sem internet / servidor indisponível → mensagem + "Tentar de novo".
- Erro ao gerar (`503`) → mensagem + "Tentar de novo".

### 7.3 Acessibilidade
- Botões com `accessibilityLabel`.
- Contraste mínimo AA entre texto e fundo.
- Transcrição serve também como alternativa para quem não pode ouvir.

---

## 8. Identidade visual

Paleta **roxo e amarelo** (herdada do PodAI), sobre fundo escuro:

| Token | Cor | Uso |
|---|---|---|
| `primaria` | `#6D28D9` (roxo) | Botão de play, destaques, logo |
| `primariaEscura` | `#2E1065` | Fundo de gradiente |
| `destaque` | `#FACC15` (amarelo) | Fala atual, "IA" do logo, barra de progresso |
| `fundo` | `#0F0A1E` | Fundo do app |
| `superficie` | `rgba(255,255,255,0.08)` | Cards em vidro (efeito *glass*: fundo translúcido + borda clara + blur com `expo-blur`) |
| `texto` | `#F5F3FF` | Texto principal |
| `textoSecundario` | `#C4B5FD` | Legendas, horários |

- **Logo:** wordmark "pod**IA**", com "IA" em amarelo; símbolo de fone de ouvido com ondas sonoras.
- Fonte: padrão do sistema ou **Inter** (`@expo-google-fonts/inter`).
- Tokens centralizados em `mobile/theme/colors.ts`.

---

## 9. Estrutura do repositório
```
podia/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI: app, CORS, startup (carrega TTS, agenda jobs)
│   │   ├── routes.py            # rotas do §5
│   │   ├── schemas.py           # modelos Pydantic de resposta
│   │   ├── db.py                # engine SQLite + sessão
│   │   ├── models.py            # tabelas SQLModel (§6)
│   │   ├── settings.py          # leitura do .env (pydantic-settings)
│   │   ├── themes.py            # carrega e valida themes.yaml
│   │   ├── scheduler.py         # APScheduler: pipeline a cada 3h + limpeza diária
│   │   └── pipeline/
│   │       ├── run.py           # orquestrador por tema (+ lock por tema)
│   │       ├── news.py          # RSS + resolução de URL + seleção
│   │       ├── extract.py       # trafilatura
│   │       ├── dialogue/
│   │       │   ├── base.py      # interface DialogueProvider + validação
│   │       │   ├── gemini.py
│   │       │   ├── groq.py
│   │       │   └── local.py     # gerador sem IA (reserva final)
│   │       ├── podia_tts/
│   │       │   ├── base.py      # interface TTSEngine
│   │       │   ├── normalize.py # números, siglas, pronúncia
│   │       │   ├── kokoro_engine.py
│   │       │   └── piper_engine.py
│   │       └── audio.py         # montagem do MP3 + tempos das falas
│   ├── config/
│   │   ├── themes.yaml
│   │   └── pronuncia.yaml
│   ├── prompts/dialogo.md
│   ├── assets/vinheta.mp3
│   ├── scripts/
│   │   └── poc_episodio.py      # Fase 0: gera 1 episódio pela linha de comando
│   ├── data/                    # podia.db + audio/ (fora do git)
│   ├── tests/
│   │   ├── fixtures/            # RSS e HTML de exemplo salvos (testes sem internet)
│   │   ├── test_news.py
│   │   ├── test_normalize.py
│   │   ├── test_dialogue.py
│   │   ├── test_audio.py
│   │   └── test_routes.py
│   ├── Dockerfile
│   ├── pyproject.toml           # dependências + config do ruff e pytest
│   └── requirements.txt
├── mobile/
│   ├── app/                     # Expo Router: index (home), player/[tema], settings
│   ├── components/              # ThemeCard, PlayerControls, Transcript, SourceCard, GlassCard
│   ├── services/api.ts          # cliente da API tipado
│   ├── hooks/                   # useLatestEpisode, useThemes
│   ├── theme/colors.ts
│   ├── types/api.ts             # tipos espelhando os schemas do backend
│   ├── assets/                  # ícone, splash, logo
│   ├── app.json
│   └── package.json
├── scripts/
│   ├── setup.sh                 # Linux/macOS: prepara .env, dependências e testes
│   └── setup.ps1                # Windows
├── docker-compose.yml
├── .env.example
├── .gitignore
├── CLAUDE.md                    # instruções curtas para o Claude Code (ver §13)
└── README.md
```

---

## 10. Configuração e variáveis de ambiente

`.env.example`:
```bash
# LLM
GEMINI_API_KEY=            # obrigatório (grátis em aistudio.google.com)
GEMINI_MODEL=gemini-flash-lite-latest   # conferir o nome do modelo gratuito vigente
GROQ_API_KEY=              # opcional (plano B)
OLLAMA_URL=                # opcional, ex.: http://host.docker.internal:11434

# Voz
TTS_ENGINE=kokoro          # kokoro | piper

# Backend
ADMIN_KEY=troque-esta-chave
SCHEDULER_INTERVAL_HOURS=3
AUDIO_RETENTION_DAYS=7
TZ=America/Cuiaba
DATA_DIR=/app/data
LOG_LEVEL=INFO

# App (mobile/.env)
EXPO_PUBLIC_API_URL=http://192.168.0.10:8000
```

---

## 11. Instalação e execução

### 11.1 Requisitos
- **Docker** e **Docker Compose** (caminho recomendado), **ou** Python 3.11+, `ffmpeg` e `espeak-ng` instalados localmente.
- **Node.js 20+** e npm para o app.
- Celular Android (com o app **Expo Go** para desenvolvimento) ou emulador do Android Studio.
- Chave gratuita do Gemini.

### 11.2 Setup rápido
```bash
# Linux / macOS
chmod +x scripts/setup.sh && ./scripts/setup.sh
```
```powershell
# Windows
.\scripts\setup.ps1
```
Os scripts: copiam `.env.example` → `.env` (se não existir), avisam se faltar `GEMINI_API_KEY`, instalam as dependências do `mobile/` e rodam os testes do backend.

### 11.3 Backend
```bash
docker compose up --build
# API em http://localhost:8000  ·  documentação em http://localhost:8000/docs
```
Sem Docker:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Na primeira execução o modelo Kokoro é baixado (~330 MB) e fica em cache no volume `data/`.

Gerar um episódio manualmente:
```bash
curl -X POST "http://localhost:8000/admin/generate?theme=futebol" -H "X-Admin-Key: $ADMIN_KEY"
# ou, sem API (Fase 0):
python scripts/poc_episodio.py --tema futebol --saida futebol.mp3
```

### 11.4 App
```bash
cd mobile
npm install
npx expo start           # escaneie o QR code com o Expo Go
```
O celular precisa acessar o backend: use o IP do notebook na mesma rede Wi-Fi (`http://192.168.x.x:8000`) ou um túnel:
```bash
cloudflared tunnel --url http://localhost:8000
```

### 11.5 Gerar o APK
```bash
cd mobile
npx eas build -p android --profile preview    # APK pelo EAS (plano grátis)
# ou build local:
npx expo prebuild && cd android && ./gradlew assembleRelease
```

---

## 12. Testes

**Backend — `pytest`** (sem internet: RSS, HTML e respostas do LLM ficam em `tests/fixtures/`; o motor de voz é substituído por um falso que gera silêncio):
| Arquivo | O que testa |
|---|---|
| `test_news.py` | Janela de 24h/72h, descarte de itens com mais de 72h, palavras bloqueadas (com e sem acento), notícia repetida, mínimo de 150 palavras |
| `test_normalize.py` | Placar, porcentagem, valores em reais, siglas, dicionário de pronúncia |
| `test_dialogue.py` | Validação do JSON, vozes inválidas, contagem de palavras, novas tentativas, troca de provedor, gerador local |
| `test_audio.py` | Pausas, tempos de cada fala, duração, ausência da vinheta |
| `test_routes.py` | Todas as rotas, `202` na geração na hora, `401` do admin, `404` |

```bash
cd backend && pytest -q
ruff check . && ruff format --check .
```

**App:** `npx tsc --noEmit` e `npx expo lint`.

**Teste manual (Fase 4):** 5–10 colegas avaliam, de 1 a 5, a naturalidade da voz, a clareza e erros percebidos; revisão manual dos episódios de Política.

---

## 13. Guia para implementação com Claude Code

### 13.1 Como usar este README
1. Crie a pasta do repositório e coloque este `README.md` na raiz.
2. Crie também o `CLAUDE.md` abaixo (o Claude Code lê esse arquivo automaticamente em toda sessão).
3. Implemente **uma fase por vez** (§14), usando os prompts do §13.3. Ao fim de cada fase: rode os testes, confira os critérios de aceite e faça commit.

### 13.2 Conteúdo sugerido para o `CLAUDE.md`
```markdown
# podIA — instruções para o Claude Code

- A especificação completa está no README.md. Siga-a; se algo for ambíguo, pergunte antes de inventar.
- Implemente apenas a fase pedida. Não adiante funcionalidades de fases futuras.
- Backend: Python 3.11, FastAPI, SQLModel, type hints em tudo, ruff para lint/format.
- App: Expo + TypeScript estrito, Expo Router, TanStack Query.
- Código e nomes técnicos em inglês; textos mostrados ao usuário, prompts e comentários de domínio em português.
- Toda etapa do pipeline é uma função testável; testes não acessam a internet (use tests/fixtures).
- Nunca coloque chaves de API no código; leia de settings.py (.env).
- Ao terminar uma tarefa: rode `pytest -q` e `ruff check .` e corrija o que falhar.
- Comandos: `docker compose up --build` · `cd backend && pytest -q` · `cd mobile && npx expo start`
```

### 13.3 Prompts por fase
Copie e cole no Claude Code, um de cada vez:

- **Fase 0:** *"Leia o README.md. Implemente a Fase 0: o script `backend/scripts/poc_episodio.py` que executa o pipeline completo para um tema (§4.1 a §4.6), usando só Gemini e Kokoro, e salva o MP3. Comece testando isoladamente a resolução de URLs do Google News (§4.2) e me mostre o resultado antes de seguir."*
- **Fase 1:** *"Implemente a Fase 1 do README: themes.yaml completo, regra de seleção, cadeia de provedores de diálogo com validação e gerador local, normalização com pronuncia.yaml e montagem com vinheta e loudnorm. Inclua os testes do §12 correspondentes."*
- **Fase 2:** *"Implemente a Fase 2 do README: FastAPI com as rotas e respostas exatas do §5, banco do §6, agendador, lock por tema, geração na hora com 202, limpeza, Dockerfile e docker-compose. Inclua test_routes.py."*
- **Fase 3:** *"Implemente a Fase 3 do README: app Expo em mobile/ com as telas do §7, a identidade do §8 e os tipos espelhando o §5.2."*
- **Fase 4/5:** *"Revise o projeto contra os critérios de aceite de todas as fases, complete os testes que faltam e atualize o §16 (Limitações) com o que descobrimos."*

---

## 14. Roadmap

Cada fase tem **critérios de aceite** objetivos: a fase só termina quando todos passam.

### Fase 0 — Prova de conceito (1 semana)
Objetivo: um MP3 bom de um tema, sem API e sem app.
- [ ] Testar a resolução de URLs do Google News (risco nº 1)
- [ ] Script `poc_episodio.py`: Futebol → notícia → texto → diálogo (Gemini) → vozes (Kokoro) → `futebol.mp3`
- [ ] Testar Kokoro com as duas vozes; gerar o mesmo diálogo com Piper e comparar
- [ ] Ajustar o prompt até o diálogo soar natural
- [ ] Normalização básica (números e siglas)
- [ ] Medir o tempo de geração de um episódio no notebook

**Aceite:** `python scripts/poc_episodio.py --tema futebol` gera um MP3 de 1:40–2:30, com as duas vozes alternando, sem fatos inventados (conferido contra a matéria), e o tempo de geração está anotado.

### Fase 1 — Pipeline para os 6 temas (1 semana)
- [ ] `themes.yaml` com os 6 temas e feeds extras conferidos
- [ ] Regra de seleção completa (janela, 72h máx., bloqueios, repetição, 150 palavras)
- [ ] Cadeia de provedores + validação + novas tentativas + gerador local
- [ ] `pronuncia.yaml` inicial
- [ ] Montagem com vinheta, loudnorm e tempos das falas
- [ ] Testes de `news`, `normalize`, `dialogue` e `audio`

**Aceite:** um comando gera 6 episódios válidos; com `GEMINI_API_KEY` vazia, o gerador local ainda produz episódios; `pytest` passa sem internet.

### Fase 2 — Backend (1–2 semanas)
- [ ] FastAPI com as rotas do §5
- [ ] SQLite com as tabelas do §6
- [ ] Agendador a cada 3h + geração inicial no startup
- [ ] Geração na hora com `202` e lock por tema
- [ ] Limpeza de áudios com mais de 7 dias
- [ ] Docker + docker-compose (com `ffmpeg` e `espeak-ng`)
- [ ] Logs por etapa (tema, etapa, duração, erro)
- [ ] `test_routes.py`

**Aceite:** após `docker compose up`, `/themes` lista os 6 temas com horário, `/docs` funciona, o áudio toca no navegador com avanço na barra, e um episódio novo surge sozinho após o intervalo (testar com `SCHEDULER_INTERVAL_HOURS` reduzido).

### Fase 3 — App Android (2 semanas)
- [ ] Projeto Expo + identidade visual (§8)
- [ ] Home com os 6 temas
- [ ] Player com segundo plano, velocidade e transcrição com destaque
- [ ] Card da fonte
- [ ] Configurações com URL do servidor e teste de conexão
- [ ] Estados de carregamento, `202` e erro
- [ ] Gerar APK

**Aceite:** APK instalado no celular toca episódios do backend pela rede Wi-Fi; o áudio continua com a tela bloqueada; desligar o backend mostra o estado de erro, sem travar.

### Fase 4 — Testes e ajustes (1 semana)
- [ ] Teste com 5–10 colegas (voz, clareza, erros)
- [ ] Revisar episódios de Política (neutralidade)
- [ ] Corrigir pronúncias recorrentes em `pronuncia.yaml`
- [ ] Completar testes automatizados

**Aceite:** nota média ≥ 3,5/5 em clareza; nenhum erro factual nos episódios revisados; testes passando.

### Fase 5 — Entrega acadêmica (1 semana)
- [ ] README revisado (este arquivo) com instruções conferidas do zero numa máquina limpa
- [ ] Documento de arquitetura e decisões (§1.3, §3, §15 como base)
- [ ] Roteiro da demonstração ao vivo (episódios gerados antes; APK já instalado; túnel testado)
- [ ] Limitações e trabalhos futuros (§16 e §17)

**Prazo total estimado:** 7–8 semanas.

---

## 15. Riscos e mitigação
| # | Risco | Prob. | Mitigação |
|---|---|---|---|
| 1 | **Não conseguir resolver os links do Google News** | Alta | Testar no dia 1; `googlenewsdecoder`; feeds diretos dos portais como fonte alternativa |
| 2 | IA inventar informações | Média | Prompt restrito à matéria; temperatura 0.4; diálogo salvo no banco; revisão na Fase 4 |
| 3 | Voz pt-BR do Kokoro soar artificial | Média | Normalização + dicionário de pronúncia; Piper como plano B; decisão na Fase 0 |
| 4 | Limite do Gemini grátis atingido ou modelo descontinuado | Média | Modelo no `.env`; Groq/Ollama; gerador local como reserva final |
| 5 | Notícia "mais recente" fraca ou curta | Média | Mínimo de 150 palavras; até 8 candidatos por rodada |
| 6 | Site bloquear a extração | Média | Passar para o próximo candidato; feeds extras |
| 7 | Política com viés | Média | Tom neutro obrigatório; atribuição de falas; revisão manual |
| 8 | Google News mudar o formato do RSS | Baixa | Feeds diretos de portais no `themes.yaml` |
| 9 | Notebook desligado ou rede ruim na demo | Média | Episódios gerados antes; túnel testado; vídeo de backup da demo |
| 10 | Direitos autorais | Baixa | Texto original nunca lido no áudio; fonte e link sempre visíveis |
| 11 | Geração lenta em CPU | Média | Medir na Fase 0; pré-geração a cada 3h esconde a latência do usuário |

---

## 16. Limitações conhecidas
- O backend precisa estar ligado e acessível; sem ele, o app não toca nada (não há modo offline no MVP).
- Uma notícia por tema: se a mais recente for pouco relevante, o episódio também será.
- A qualidade da voz depende do motor escolhido; nomes estrangeiros podem sair errados até entrarem no `pronuncia.yaml`.
- O plano gratuito do Gemini pode mudar de limites ou modelos.
- O gerador local (sem IA) produz episódios curtos e mais "secos" — é só uma reserva.

---

## 17. Melhorias futuras (pós-trabalho)
1. Preferir notícias cobertas por 2+ veículos (relevância)
2. Giro com 2–3 notícias por episódio
3. Mais temas (Economia, Ciência, Saúde…)
4. Favoritos e histórico
5. Download offline dos episódios
6. Notificação de episódio novo
7. Versão iOS (o Expo já permite)
8. Hospedagem 24h (Oracle Always Free)
9. Modo "sem servidor" com TTS do aparelho como reserva (abordagem do PodAI)

---

*Episódios do podIA são gerados por IA a partir das fontes indicadas e podem conter imprecisões. Consulte sempre a matéria original.*
