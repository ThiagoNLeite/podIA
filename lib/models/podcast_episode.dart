import 'news_article.dart';
import 'podcast_theme.dart';

/// Tipo de trecho do roteiro.
enum SegmentKind { intro, news, filler, outro }

/// Um parágrafo do roteiro, falado como uma unidade pelo TTS.
class ScriptSegment {
  const ScriptSegment({required this.kind, required this.text, this.article});

  final SegmentKind kind;
  final String text;

  /// Notícia associada (apenas quando [kind] == [SegmentKind.news]).
  final NewsArticle? article;

  int get wordCount => countWords(text);
}

/// Conta palavras separadas por espaço em branco.
int countWords(String text) =>
    text.split(RegExp(r'\s+')).where((w) => w.trim().isNotEmpty).length;

/// Episódio pronto para ser reproduzido.
class PodcastEpisode {
  const PodcastEpisode({
    required this.theme,
    required this.articles,
    required this.segments,
    required this.generatedAt,
    required this.generatedByAi,
  });

  final PodcastTheme theme;
  final List<NewsArticle> articles;
  final List<ScriptSegment> segments;
  final DateTime generatedAt;

  /// `true` quando o roteiro veio de um modelo de IA (e não do gerador local).
  final bool generatedByAi;

  List<String> get paragraphs => segments.map((s) => s.text).toList();

  String get fullText => paragraphs.join('\n\n');

  int get wordCount => segments.fold(0, (sum, s) => sum + s.wordCount);

  /// Estimativa de duração dada uma velocidade em palavras por minuto.
  Duration estimatedDuration({required double wordsPerMinute}) {
    final seconds = wordCount / wordsPerMinute * 60;
    return Duration(seconds: seconds.round());
  }
}
