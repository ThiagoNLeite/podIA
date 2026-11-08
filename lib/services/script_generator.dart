import 'package:intl/intl.dart';

import '../models/news_article.dart';
import '../models/podcast_episode.dart';
import '../models/podcast_theme.dart';

/// Monta o roteiro do episódio (em português) a partir das notícias.
///
/// O gerador funciona totalmente offline. Ele controla o número de palavras
/// para que a narração fique perto de 2 minutos na velocidade escolhida.
class ScriptGenerator {
  const ScriptGenerator({
    this.targetWords = 300,
    this.minArticles = 3,
    this.maxArticles = 8,
  });

  /// Palavras-alvo. A ~150 palavras por minuto, 300 palavras ≈ 2 minutos.
  final int targetWords;
  final int minArticles;
  final int maxArticles;

  static const _openers = [
    'Começando pela manchete principal:',
    'Em seguida,',
    'Outra notícia que chamou a atenção:',
    'Também nas últimas horas,',
    'Continuando o giro de notícias,',
    'Mais um destaque:',
    'E ainda:',
    'Para fechar o bloco,',
  ];

  static const _fillers = [
    'Lembrando que todas as notícias desta edição foram publicadas nas últimas '
        'setenta e duas horas, e você pode conferir as matérias completas pelos '
        'links disponíveis na tela do episódio.',
    'Se algum desses assuntos despertou seu interesse, vale acompanhar os '
        'desdobramentos ao longo dos próximos dias, porque esse podcast é '
        'atualizado a cada nova geração com o que há de mais recente.',
    'E se você quiser ouvir sobre outros assuntos, é só voltar à tela inicial '
        'e escolher um dos seis temas disponíveis.',
  ];

  List<ScriptSegment> build({
    required PodcastTheme theme,
    required List<NewsArticle> articles,
    DateTime? now,
  }) {
    final reference = now ?? DateTime.now();
    final intro = ScriptSegment(
      kind: SegmentKind.intro,
      text: _intro(theme, articles.length, reference),
    );
    final outro = ScriptSegment(kind: SegmentKind.outro, text: _outro(theme));

    final segments = <ScriptSegment>[intro];
    var words = intro.wordCount + outro.wordCount;

    for (var i = 0; i < articles.length && i < maxArticles; i++) {
      final segment = ScriptSegment(
        kind: SegmentKind.news,
        text: _news(i, articles[i], reference),
        article: articles[i],
      );
      final newsSoFar = segments.length - 1;
      final wouldExceed = words + segment.wordCount > targetWords + 40;
      if (wouldExceed && newsSoFar >= minArticles) break;
      segments.add(segment);
      words += segment.wordCount;
    }

    for (final filler in _fillers) {
      if (words >= targetWords - 25) break;
      final segment = ScriptSegment(kind: SegmentKind.filler, text: filler);
      segments.add(segment);
      words += segment.wordCount;
    }

    segments.add(outro);
    return segments;
  }

  String _intro(PodcastTheme theme, int total, DateTime now) {
    final date = DateFormat("EEEE, d 'de' MMMM", 'pt_BR').format(now);
    final hour = DateFormat('HH:mm', 'pt_BR').format(now);
    return 'Olá! Este é o seu podcast de ${theme.name}. '
        'Hoje é $date, e são $hour. '
        'Nos próximos dois minutos você fica por dentro das principais '
        'notícias sobre ${theme.name.toLowerCase()} publicadas nas últimas '
        'setenta e duas horas. Vamos lá!';
  }

  String _news(int index, NewsArticle article, DateTime now) {
    final opener = _openers[index % _openers.length];
    final headline = _normalizeSentence(article.title);
    final buffer = StringBuffer('$opener $headline. ')
      ..write('A informação é de ${article.source}, publicada '
          '${article.relativeTime(now: now)}.');
    final summary = article.summary;
    if (summary != null && summary.isNotEmpty) {
      buffer.write(' Segundo a publicação, ${_normalizeSentence(summary)}.');
    }
    return buffer.toString();
  }

  String _outro(PodcastTheme theme) =>
      'E por hoje é só. Essas foram as principais notícias de '
      '${theme.name.toLowerCase()} das últimas setenta e duas horas. '
      'Obrigado por ouvir, e até o próximo episódio!';

  /// Remove pontuação final duplicada e espaços extras.
  static String _normalizeSentence(String text) {
    var t = text.trim().replaceAll(RegExp(r'\s+'), ' ');
    t = t.replaceAll(RegExp(r'[.!?…]+$'), '');
    return t;
  }

  /// Converte um texto livre (por exemplo, vindo de um modelo de IA) em
  /// segmentos, um por parágrafo.
  static List<ScriptSegment> fromPlainText(String text) {
    final paragraphs = text
        .split(RegExp(r'\n\s*\n|\r\n\s*\r\n'))
        .map((p) => p.replaceAll(RegExp(r'\s+'), ' ').trim())
        .where((p) => p.isNotEmpty)
        .toList();
    if (paragraphs.isEmpty) return const [];
    return [
      for (var i = 0; i < paragraphs.length; i++)
        ScriptSegment(
          kind: i == 0
              ? SegmentKind.intro
              : i == paragraphs.length - 1
                  ? SegmentKind.outro
                  : SegmentKind.news,
          text: paragraphs[i],
        ),
    ];
  }
}
