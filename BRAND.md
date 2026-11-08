# Identidade visual — PodAI

## Conceito

**PodAI** = *Podcast* + *AI*. A marca transmite "notícias transformadas em
áudio por inteligência": um microfone de vidro translúcido (liquid glass)
sobre um fundo roxo profundo, com uma faísca e ondas sonoras em amarelo.

- **Roxo** → tecnologia, IA, profundidade e sofisticação.
- **Amarelo** → energia, voz, informação em destaque.
- **Liquid glass** → painéis translúcidos com desfoque do fundo, borda
  luminosa e reflexo no topo, flutuando sobre "bolhas" de luz desfocadas.

## Paleta

| Nome | Hex | Uso |
|------|-----|-----|
| Deep Purple | `#2E1065` | fundo base, barra de navegação, splash |
| Purple | `#5B21B6` | fim do gradiente de fundo |
| Violet | `#7C3AED` | símbolo da logo, bolhas de luz, snackbars |
| Lavender | `#C4B5FD` | textos secundários |
| Yellow | `#FACC15` | destaque principal: botão play, sliders, chips, ícones de seção |
| Light Yellow | `#FDE68A` | títulos de seção, início do gradiente de destaque |
| Amber | `#F59E0B` | fim do gradiente de destaque |

Gradiente de fundo: `#1E0A47 → #2E1065 → #5B21B6` (diagonal).
Gradiente de destaque: `#FDE68A → #FACC15 → #F59E0B`.

Vidro: preenchimento `white 12 %` (ou 20 % em painéis fortes), borda
`white 33 %`, blur 18 px, reflexo `white 18 % → 0 %` nos 60 px superiores,
sombra `black 33 %` com blur 24 px.

## Logotipo

- **Símbolo**: quadrado arredondado (raio 28 %) com gradiente violeta→roxo,
  microfone branco e faísca amarela no canto superior direito.
  Implementado em `lib/widgets/podai_logo.dart` (`PodAiMark`).
- **Wordmark**: "Pod" em branco + "AI" com gradiente amarelo, peso 800,
  espaçamento -0,5 (`PodAiWordmark`).
- **Ícone do app**: `assets/icon/podai_icon.png` (1024×1024), aplicado com
  `dart run flutter_launcher_icons`.

## Tipografia e formas

- Fonte padrão do sistema (Roboto / SF Pro), títulos em peso 700–800.
- Raios: painéis 24 px, campos e botões 16 px, chips em pílula.
- Ícones Material arredondados (`*_rounded`).

## Onde está no código

| Arquivo | Conteúdo |
|---------|----------|
| `lib/theme/app_theme.dart` | paleta (`PodAiColors`) e `ThemeData` (`PodAiTheme`) |
| `lib/widgets/glass.dart` | `PodAiBackground`, `GlassPanel`, `GlassIconButton`, `GlassChip` |
| `lib/widgets/podai_logo.dart` | `PodAiLogo`, `PodAiMark`, `PodAiWordmark` |
| `android/app/src/main/res/` | splash e cores de sistema no Android |
