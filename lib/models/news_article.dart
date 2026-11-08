/// Uma notícia obtida do feed RSS.
class NewsArticle {
  const NewsArticle({
    required this.title,
    required this.source,
    required this.link,
    required this.publishedAt,
    this.summary,
  });

  final String title;
  final String source;
  final String link;
  final DateTime publishedAt;

  /// Texto complementar (pode ser nulo quando o feed só traz a manchete).
  final String? summary;

  /// Quanto tempo se passou desde a publicação.
  Duration ageAt(DateTime now) => now.difference(publishedAt);

  /// `true` se a notícia foi publicada dentro da janela informada.
  bool isWithin(Duration window, {DateTime? now}) {
    final reference = now ?? DateTime.now();
    final age = ageAt(reference);
    return !age.isNegative && age <= window;
  }

  /// Texto em português do tipo "há 3 horas".
  String relativeTime({DateTime? now}) {
    final age = ageAt(now ?? DateTime.now());
    if (age.inMinutes < 1) return 'há instantes';
    if (age.inMinutes < 60) {
      final m = age.inMinutes;
      return 'há $m ${m == 1 ? 'minuto' : 'minutos'}';
    }
    if (age.inHours < 24) {
      final h = age.inHours;
      return 'há $h ${h == 1 ? 'hora' : 'horas'}';
    }
    final d = age.inDays;
    return 'há $d ${d == 1 ? 'dia' : 'dias'}';
  }
}
