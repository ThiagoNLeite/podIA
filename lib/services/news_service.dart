import 'dart:io' show HttpDate;

import 'package:http/http.dart' as http;
import 'package:xml/xml.dart';

import '../data/themes.dart';
import '../models/news_article.dart';
import '../models/podcast_theme.dart';

/// Erro amigável lançado quando não é possível obter notícias.
class NewsException implements Exception {
  NewsException(this.message);
  final String message;

  @override
  String toString() => message;
}

/// Busca notícias no feed RSS do Google Notícias e aplica a regra das 72h.
///
/// Não exige chave de API. O feed já aceita o filtro `when:3d`, e o
/// aplicativo ainda valida a data de cada item localmente para garantir
/// que nada com mais de [kMaxArticleAge] entre no episódio.
class NewsService {
  NewsService({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  static const _language = 'pt-BR';
  static const _country = 'BR';
  static const _ceid = 'BR:pt-419';

  Uri buildFeedUri(PodcastTheme theme) {
    final query = '${theme.query} when:3d';
    return Uri.https('news.google.com', '/rss/search', {
      'q': query,
      'hl': _language,
      'gl': _country,
      'ceid': _ceid,
    });
  }

  /// Retorna até [limit] notícias, da mais recente para a mais antiga,
  /// todas publicadas dentro de [kMaxArticleAge].
  Future<List<NewsArticle>> fetchRecent(
    PodcastTheme theme, {
    int limit = 10,
    DateTime? now,
  }) async {
    final uri = buildFeedUri(theme);
    http.Response response;
    try {
      response = await _client
          .get(uri, headers: {'User-Agent': 'NewsPodcastApp/1.0'})
          .timeout(const Duration(seconds: 20));
    } catch (_) {
      throw NewsException(
        'Não foi possível conectar ao serviço de notícias. '
        'Verifique sua conexão com a internet.',
      );
    }
    if (response.statusCode != 200) {
      throw NewsException(
        'O serviço de notícias respondeu com erro (${response.statusCode}).',
      );
    }

    final all = parseRss(response.body);
    final reference = now ?? DateTime.now();
    final recent = filterRecent(all, now: reference);
    if (recent.isEmpty) {
      throw NewsException(
        'Nenhuma notícia sobre ${theme.name} foi publicada nas últimas 72 horas.',
      );
    }
    return recent.take(limit).toList();
  }

  /// Mantém apenas notícias dentro da janela, remove duplicadas e ordena.
  static List<NewsArticle> filterRecent(
    List<NewsArticle> articles, {
    required DateTime now,
    Duration window = kMaxArticleAge,
  }) {
    final seen = <String>{};
    final result = <NewsArticle>[];
    for (final article in articles) {
      if (!article.isWithin(window, now: now)) continue;
      final key = article.title.toLowerCase().trim();
      if (!seen.add(key)) continue;
      result.add(article);
    }
    result.sort((a, b) => b.publishedAt.compareTo(a.publishedAt));
    return result;
  }

  /// Converte o XML do RSS em objetos [NewsArticle].
  static List<NewsArticle> parseRss(String xml) {
    final XmlDocument document;
    try {
      document = XmlDocument.parse(xml);
    } on XmlException {
      throw NewsException('O feed de notícias retornou um formato inválido.');
    }

    final items = document.findAllElements('item');
    final articles = <NewsArticle>[];
    for (final item in items) {
      final rawTitle = _text(item, 'title');
      final link = _text(item, 'link');
      final pubDate = _text(item, 'pubDate');
      if (rawTitle.isEmpty || pubDate.isEmpty) continue;

      final publishedAt = _parseDate(pubDate);
      if (publishedAt == null) continue;

      final sourceElement = _text(item, 'source');
      final split = _splitTitleAndSource(rawTitle);
      final source = sourceElement.isNotEmpty ? sourceElement : split.$2;
      final title = split.$1;

      final summary = _cleanSummary(
        _text(item, 'description'),
        title: title,
        source: source,
      );

      articles.add(NewsArticle(
        title: title,
        source: source.isEmpty ? 'fonte não informada' : source,
        link: link,
        publishedAt: publishedAt,
        summary: summary,
      ));
    }
    return articles;
  }

  static String _text(XmlElement parent, String name) {
    final element = parent.getElement(name);
    if (element == null) return '';
    return element.innerText.trim();
  }

  /// Datas em RSS seguem o formato RFC 822 ("Sat, 18 Oct 2026 12:00:00 GMT").
  static DateTime? _parseDate(String raw) {
    try {
      return HttpDate.parse(raw).toLocal();
    } catch (_) {
      return DateTime.tryParse(raw)?.toLocal();
    }
  }

  /// O Google Notícias formata o título como "Manchete - Fonte".
  static (String, String) _splitTitleAndSource(String rawTitle) {
    final index = rawTitle.lastIndexOf(' - ');
    if (index <= 0) return (rawTitle, '');
    final title = rawTitle.substring(0, index).trim();
    final source = rawTitle.substring(index + 3).trim();
    return (title, source);
  }

  /// Remove HTML do resumo e descarta textos que apenas repetem a manchete.
  static String? _cleanSummary(
    String html, {
    required String title,
    required String source,
  }) {
    if (html.isEmpty) return null;
    var text = stripHtml(html);
    text = text.replaceAll(title, ' ');
    if (source.isNotEmpty) text = text.replaceAll(source, ' ');
    text = text.replaceAll(RegExp(r'\s+'), ' ').trim();
    text = text.replaceAll(RegExp(r'^[\s\-–—:·|]+'), '').trim();
    if (text.length < 40) return null;

    // Garante um trecho curto, terminado em frase completa quando possível.
    if (text.length > 220) {
      final cut = text.substring(0, 220);
      final lastStop = cut.lastIndexOf(RegExp(r'[.!?]'));
      text = lastStop > 80 ? cut.substring(0, lastStop + 1) : '$cut…';
    }
    return text;
  }

  /// Remove tags HTML e decodifica as entidades mais comuns.
  static String stripHtml(String html) {
    var text = html
        .replaceAll(RegExp(r'<br\s*/?>', caseSensitive: false), ' ')
        .replaceAll(RegExp(r'</(p|li|div|h\d)>', caseSensitive: false), '. ')
        .replaceAll(RegExp(r'<[^>]+>'), ' ');
    const entities = {
      '&nbsp;': ' ',
      '&amp;': '&',
      '&quot;': '"',
      '&#39;': "'",
      '&apos;': "'",
      '&lt;': '<',
      '&gt;': '>',
    };
    entities.forEach((k, v) => text = text.replaceAll(k, v));
    text = text.replaceAllMapped(
      RegExp(r'&#(\d+);'),
      (m) => String.fromCharCode(int.parse(m.group(1)!)),
    );
    return text.replaceAll(RegExp(r'\s+'), ' ').trim();
  }

  void dispose() => _client.close();
}
