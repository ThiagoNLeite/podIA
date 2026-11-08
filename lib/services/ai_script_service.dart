import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/news_article.dart';
import '../models/podcast_theme.dart';

/// Gera o roteiro com um modelo de linguagem (API compatível com OpenAI).
///
/// É opcional: só é usado quando o usuário informa uma chave em Configurações.
/// Em caso de falha, o aplicativo recorre ao [ScriptGenerator] local.
class AiScriptService {
  AiScriptService({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  static final Uri _endpoint =
      Uri.parse('https://api.openai.com/v1/chat/completions');

  Future<String> generate({
    required String apiKey,
    required PodcastTheme theme,
    required List<NewsArticle> articles,
    required int targetWords,
    String model = 'gpt-4o-mini',
  }) async {
    final now = DateTime.now();
    final headlines = articles
        .map((a) {
          final summary = a.summary == null ? '' : ' Resumo: ${a.summary}';
          return '- ${a.title} (${a.source}, ${a.relativeTime(now: now)}).$summary';
        })
        .join('\n');

    final body = jsonEncode({
      'model': model,
      'temperature': 0.7,
      'messages': [
        {
          'role': 'system',
          'content':
              'Você é o roteirista de um podcast diário de notícias em português '
                  'do Brasil. Escreva um roteiro para ser lido em voz alta por '
                  'uma única pessoa, com aproximadamente $targetWords palavras '
                  '(cerca de dois minutos de áudio). Use parágrafos curtos '
                  'separados por linha em branco: uma abertura, um parágrafo '
                  'por notícia e um encerramento. Cite a fonte de cada notícia. '
                  'Não invente fatos que não estejam nas manchetes. Não use '
                  'marcadores, títulos, emojis nem indicações como "[música]".',
        },
        {
          'role': 'user',
          'content': 'Tema: ${theme.name}.\n'
              'Notícias publicadas nas últimas 72 horas:\n$headlines',
        },
      ],
    });

    final response = await _client
        .post(
          _endpoint,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $apiKey',
          },
          body: body,
        )
        .timeout(const Duration(seconds: 60));

    if (response.statusCode != 200) {
      throw Exception('API de IA respondeu ${response.statusCode}');
    }
    final json = jsonDecode(utf8.decode(response.bodyBytes)) as Map;
    final choices = json['choices'] as List?;
    if (choices == null || choices.isEmpty) {
      throw Exception('API de IA não retornou conteúdo');
    }
    final content =
        ((choices.first as Map)['message'] as Map)['content'] as String?;
    if (content == null || content.trim().isEmpty) {
      throw Exception('API de IA retornou roteiro vazio');
    }
    return content.trim();
  }

  void dispose() => _client.close();
}
