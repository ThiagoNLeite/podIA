import 'package:flutter_test/flutter_test.dart';
import 'package:news_podcast_app/models/news_article.dart';
import 'package:news_podcast_app/services/news_service.dart';

void main() {
  group('Regra das 72 horas', () {
    final now = DateTime(2026, 10, 19, 20, 0);

    NewsArticle article(String title, Duration age) => NewsArticle(
          title: title,
          source: 'Fonte',
          link: 'https://example.com',
          publishedAt: now.subtract(age),
        );

    test('mantém apenas notícias com até 72h e ordena da mais recente', () {
      final result = NewsService.filterRecent([
        article('Antiga', const Duration(hours: 73)),
        article('Limite', const Duration(hours: 72)),
        article('Recente', const Duration(hours: 1)),
        article('Ontem', const Duration(hours: 30)),
      ], now: now);

      expect(result.map((a) => a.title), ['Recente', 'Ontem', 'Limite']);
    });

    test('remove manchetes duplicadas', () {
      final result = NewsService.filterRecent([
        article('Mesma manchete', const Duration(hours: 2)),
        article('mesma manchete', const Duration(hours: 5)),
      ], now: now);

      expect(result, hasLength(1));
    });

    test('descarta datas no futuro', () {
      final result = NewsService.filterRecent([
        article('Futuro', const Duration(hours: -2)),
      ], now: now);

      expect(result, isEmpty);
    });
  });

  group('Parsing do RSS', () {
    const xml = '''
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>"tecnologia" - Google Notícias</title>
    <item>
      <title>Nova IA bate recorde em teste - Portal Tech</title>
      <link>https://news.google.com/rss/articles/abc</link>
      <pubDate>Sun, 18 Oct 2026 12:00:00 GMT</pubDate>
      <description>&lt;a href="x"&gt;Nova IA bate recorde em teste&lt;/a&gt;&amp;nbsp;&amp;nbsp;&lt;font color="#6f6f6f"&gt;Portal Tech&lt;/font&gt;</description>
      <source url="https://portaltech.example">Portal Tech</source>
    </item>
    <item>
      <title>Sem data</title>
      <link>https://example.com</link>
    </item>
  </channel>
</rss>
''';

    test('separa manchete, fonte e data; ignora itens sem data', () {
      final articles = NewsService.parseRss(xml);

      expect(articles, hasLength(1));
      final a = articles.single;
      expect(a.title, 'Nova IA bate recorde em teste');
      expect(a.source, 'Portal Tech');
      expect(a.publishedAt.toUtc(), DateTime.utc(2026, 10, 18, 12));
      // A descrição só repete a manchete, então não vira resumo.
      expect(a.summary, isNull);
    });

    test('stripHtml remove tags e entidades', () {
      expect(
        NewsService.stripHtml('<p>Ol&#225;&nbsp;<b>mundo</b> &amp; cia</p>'),
        'Olá mundo & cia.',
      );
    });
  });

  group('Tempo relativo', () {
    final now = DateTime(2026, 10, 19, 20, 0);

    test('formata em português', () {
      NewsArticle at(Duration age) => NewsArticle(
            title: 't',
            source: 's',
            link: '',
            publishedAt: now.subtract(age),
          );
      expect(at(const Duration(minutes: 1)).relativeTime(now: now),
          'há 1 minuto');
      expect(at(const Duration(hours: 3)).relativeTime(now: now),
          'há 3 horas');
      expect(at(const Duration(hours: 50)).relativeTime(now: now),
          'há 2 dias');
    });
  });
}
