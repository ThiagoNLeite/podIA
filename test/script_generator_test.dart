import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:news_podcast_app/data/themes.dart';
import 'package:news_podcast_app/models/news_article.dart';
import 'package:news_podcast_app/models/podcast_episode.dart';
import 'package:news_podcast_app/services/script_generator.dart';

void main() {
  setUpAll(() => initializeDateFormatting('pt_BR'));

  final now = DateTime(2026, 10, 19, 20, 0);

  List<NewsArticle> fakeArticles(int count) => List.generate(
        count,
        (i) => NewsArticle(
          title: 'Manchete número ${i + 1} sobre um assunto relevante do dia',
          source: 'Jornal $i',
          link: 'https://example.com/$i',
          publishedAt: now.subtract(Duration(hours: i * 5 + 1)),
          summary: i.isEven
              ? 'um detalhe adicional sobre a manchete que ajuda a contextualizar o ouvinte'
              : null,
        ),
      );

  test('há exatamente 6 temas predefinidos', () {
    expect(kPodcastThemes, hasLength(6));
    expect(kPodcastThemes.map((t) => t.id).toSet(), hasLength(6));
  });

  test('o roteiro fica perto de 300 palavras (~2 min a 150 ppm)', () {
    const generator = ScriptGenerator(targetWords: 300);
    final segments = generator.build(
      theme: kPodcastThemes.first,
      articles: fakeArticles(10),
      now: now,
    );
    final episode = PodcastEpisode(
      theme: kPodcastThemes.first,
      articles: fakeArticles(10),
      segments: segments,
      generatedAt: now,
      generatedByAi: false,
    );

    expect(episode.wordCount, inInclusiveRange(240, 360));
    final duration = episode.estimatedDuration(wordsPerMinute: 150);
    expect(duration.inSeconds, inInclusiveRange(95, 145));
  });

  test('começa com abertura, termina com encerramento e cita as fontes', () {
    const generator = ScriptGenerator();
    final segments = generator.build(
      theme: kPodcastThemes[1],
      articles: fakeArticles(4),
      now: now,
    );

    expect(segments.first.kind, SegmentKind.intro);
    expect(segments.last.kind, SegmentKind.outro);
    expect(segments.first.text, contains('Economia'));
    final news = segments.where((s) => s.kind == SegmentKind.news).toList();
    expect(news.length, greaterThanOrEqualTo(3));
    expect(news.first.text, contains('Jornal 0'));
    expect(news.first.text, contains('há 1 hora'));
  });

  test('com poucas notícias, completa o tempo com trechos de preenchimento',
      () {
    const generator = ScriptGenerator(targetWords: 300);
    final segments = generator.build(
      theme: kPodcastThemes[2],
      articles: fakeArticles(1),
      now: now,
    );

    expect(segments.any((s) => s.kind == SegmentKind.filler), isTrue);
  });

  test('fromPlainText divide por parágrafos', () {
    final segments = ScriptGenerator.fromPlainText(
      'Abertura.\n\nNotícia um.\n\nNotícia dois.\n\nEncerramento.',
    );
    expect(segments, hasLength(4));
    expect(segments.first.kind, SegmentKind.intro);
    expect(segments.last.kind, SegmentKind.outro);
    expect(segments[1].kind, SegmentKind.news);
  });
}
