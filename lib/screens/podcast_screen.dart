import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../data/themes.dart';
import '../models/news_article.dart';
import '../models/podcast_episode.dart';
import '../models/podcast_theme.dart';
import '../services/ai_script_service.dart';
import '../services/app_settings.dart';
import '../services/news_service.dart';
import '../services/script_generator.dart';
import '../services/tts_service.dart';
import '../theme/app_theme.dart';
import '../widgets/glass.dart';
import '../widgets/podai_logo.dart';

enum _Stage { fetching, writing, ready, error }

class PodcastScreen extends StatefulWidget {
  const PodcastScreen({super.key, required this.theme});

  final PodcastTheme theme;

  @override
  State<PodcastScreen> createState() => _PodcastScreenState();
}

class _PodcastScreenState extends State<PodcastScreen> {
  final _newsService = NewsService();
  final _aiService = AiScriptService();
  late final TtsService _tts;

  _Stage _stage = _Stage.fetching;
  String? _error;
  PodcastEpisode? _episode;
  bool _showScript = true;

  @override
  void initState() {
    super.initState();
    _tts = context.read<TtsService>();
    _generate();
  }

  @override
  void dispose() {
    _tts.stop();
    _newsService.dispose();
    _aiService.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    final tts = _tts;
    final settings = context.read<AppSettings>();
    await tts.stop();

    setState(() {
      _stage = _Stage.fetching;
      _error = null;
      _episode = null;
    });

    try {
      final articles = await _newsService.fetchRecent(widget.theme);
      if (!mounted) return;
      setState(() => _stage = _Stage.writing);

      // Dimensiona o roteiro para ~2 minutos na velocidade de voz atual.
      final targetWords =
          (kTargetEpisodeDuration.inSeconds / 60 * tts.wordsPerMinute).round();
      final generator = ScriptGenerator(targetWords: targetWords);

      List<ScriptSegment> segments = const [];
      var usedAi = false;
      if (settings.useAi) {
        try {
          final text = await _aiService.generate(
            apiKey: settings.openAiApiKey,
            theme: widget.theme,
            articles: articles,
            targetWords: targetWords,
          );
          segments = ScriptGenerator.fromPlainText(text);
          usedAi = segments.isNotEmpty;
        } catch (e) {
          debugPrint('Falha na IA, usando gerador local: $e');
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text(
                  'Não foi possível usar a IA. Roteiro gerado localmente.'),
            ));
          }
        }
      }
      if (segments.isEmpty) {
        segments = generator.build(theme: widget.theme, articles: articles);
      }

      if (!mounted) return;
      setState(() {
        _episode = PodcastEpisode(
          theme: widget.theme,
          articles: articles,
          segments: segments,
          generatedAt: DateTime.now(),
          generatedByAi: usedAi,
        );
        _stage = _Stage.ready;
      });

      if (!await tts.hasPortugueseVoice() && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Nenhuma voz em português foi encontrada. Instale uma nas '
              'configurações de texto para voz do aparelho.'),
          duration: Duration(seconds: 6),
        ));
      }
    } on NewsException catch (e) {
      if (!mounted) return;
      setState(() {
        _stage = _Stage.error;
        _error = e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _stage = _Stage.error;
        _error = 'Ocorreu um erro inesperado: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = widget.theme;
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Row(
          children: [
            Icon(theme.icon, color: theme.color, size: 22),
            const SizedBox(width: 8),
            Text(theme.name),
          ],
        ),
        actions: [
          if (_stage == _Stage.ready)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: GlassIconButton(
                tooltip: 'Gerar novamente',
                icon: Icons.refresh_rounded,
                size: 42,
                iconSize: 20,
                onPressed: _generate,
              ),
            ),
        ],
      ),
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 350),
        child: switch (_stage) {
          _Stage.fetching => const _Loading(
              key: ValueKey('fetching'), message: 'Buscando notícias…'),
          _Stage.writing => const _Loading(
              key: ValueKey('writing'), message: 'Escrevendo o roteiro…'),
          _Stage.error => _ErrorView(
              key: const ValueKey('error'),
              message: _error!,
              onRetry: _generate),
          _Stage.ready => _buildEpisode(context, _episode!),
        },
      ),
    );
  }

  Widget _buildEpisode(BuildContext context, PodcastEpisode episode) {
    final tts = context.watch<TtsService>();
    final duration =
        episode.estimatedDuration(wordsPerMinute: tts.wordsPerMinute);

    return ListView(
      key: const ValueKey('ready'),
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        _PlayerCard(episode: episode, duration: duration, tts: tts),
        const SizedBox(height: 24),
        _SectionHeader(
          title: 'Roteiro',
          icon: Icons.description_outlined,
          actions: [
            GlassIconButton(
              tooltip: 'Copiar roteiro',
              icon: Icons.copy_rounded,
              size: 38,
              iconSize: 18,
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: episode.fullText));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                      content: Text('Roteiro copiado.')));
                }
              },
            ),
            const SizedBox(width: 8),
            GlassIconButton(
              tooltip: _showScript ? 'Ocultar' : 'Mostrar',
              icon: _showScript
                  ? Icons.expand_less_rounded
                  : Icons.expand_more_rounded,
              size: 38,
              iconSize: 20,
              onPressed: () => setState(() => _showScript = !_showScript),
            ),
          ],
        ),
        if (_showScript)
          GlassPanel(
            padding: const EdgeInsets.all(8),
            child: Column(
              children: List.generate(episode.segments.length, (i) {
                return _SegmentTile(
                  segment: episode.segments[i],
                  isCurrent: tts.currentIndex == i,
                  accent: widget.theme.color,
                );
              }),
            ),
          ),
        const SizedBox(height: 24),
        _SectionHeader(
          title: 'Fontes (${episode.articles.length})',
          icon: Icons.newspaper_rounded,
        ),
        GlassPanel(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Column(
            children: [
              for (var i = 0; i < episode.articles.length; i++) ...[
                _ArticleTile(article: episode.articles[i]),
                if (i < episode.articles.length - 1)
                  const Divider(height: 1, indent: 52),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.title,
    required this.icon,
    this.actions = const [],
  });

  final String title;
  final IconData icon;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 0, 0, 10),
      child: Row(
        children: [
          Icon(icon, size: 18, color: PodAiColors.yellow),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              title,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: PodAiColors.lightYellow,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.4,
                  ),
            ),
          ),
          ...actions,
        ],
      ),
    );
  }
}

class _PlayerCard extends StatelessWidget {
  const _PlayerCard({
    required this.episode,
    required this.duration,
    required this.tts,
  });

  final PodcastEpisode episode;
  final Duration duration;
  final TtsService tts;

  @override
  Widget build(BuildContext context) {
    final theme = episode.theme;
    final textTheme = Theme.of(context).textTheme;
    final minutes = duration.inMinutes;
    final seconds = (duration.inSeconds % 60).toString().padLeft(2, '0');
    final progress = tts.state == PlaybackState.completed ? 1.0 : tts.progress;

    return GlassPanel(
      strong: true,
      tint: theme.color,
      borderColor: theme.color.withOpacity(0.5),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _EpisodeArt(theme: theme, playing: tts.isPlaying),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const PodAiWordmark(fontSize: 14),
                    const SizedBox(height: 2),
                    Text(
                      'Episódio de ${theme.name}',
                      style: textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: [
                        GlassChip(
                            icon: Icons.timer_outlined,
                            label: '~$minutes:$seconds'),
                        GlassChip(
                            icon: Icons.newspaper_rounded,
                            label: '${episode.articles.length} notícias'),
                        GlassChip(
                            icon: episode.generatedByAi
                                ? Icons.auto_awesome
                                : Icons.phone_android_rounded,
                            label: episode.generatedByAi
                                ? 'roteiro IA'
                                : 'no aparelho'),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 22),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: Stack(
              children: [
                Container(height: 8, color: PodAiColors.glassFillStrong),
                AnimatedFractionallySizedBox(
                  duration: const Duration(milliseconds: 400),
                  curve: Curves.easeOut,
                  widthFactor: progress.clamp(0.0, 1.0),
                  child: Container(
                    height: 8,
                    decoration: BoxDecoration(
                      gradient: PodAiColors.accent,
                      boxShadow: [
                        BoxShadow(
                          color: PodAiColors.yellow.withOpacity(0.6),
                          blurRadius: 10,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Text(
                switch (tts.state) {
                  PlaybackState.idle => 'Toque para ouvir',
                  PlaybackState.playing => 'Reproduzindo…',
                  PlaybackState.paused => 'Pausado',
                  PlaybackState.completed => 'Episódio concluído',
                },
                style: textTheme.labelMedium
                    ?.copyWith(color: PodAiColors.lavender),
              ),
              const Spacer(),
              Text(
                '${episode.wordCount} palavras · 72h',
                style: textTheme.labelMedium
                    ?.copyWith(color: PodAiColors.lavender),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              GlassIconButton(
                tooltip: 'Parar',
                icon: Icons.stop_rounded,
                onPressed:
                    tts.state == PlaybackState.idle ? null : () => tts.stop(),
              ),
              const SizedBox(width: 22),
              GlassIconButton(
                tooltip: tts.isPlaying ? 'Pausar' : 'Reproduzir',
                primary: true,
                size: 76,
                iconSize: 40,
                icon: tts.isPlaying
                    ? Icons.pause_rounded
                    : Icons.play_arrow_rounded,
                onPressed: () {
                  if (tts.isPlaying) {
                    tts.pause();
                  } else if (tts.isPaused) {
                    tts.resume();
                  } else {
                    tts.play(episode.paragraphs);
                  }
                },
              ),
              const SizedBox(width: 22),
              GlassIconButton(
                tooltip: 'Reiniciar',
                icon: Icons.replay_rounded,
                onPressed: () => tts.play(episode.paragraphs),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// "Capa" do episódio: ícone do tema sobre um disco de vidro, com um anel
/// amarelo pulsante enquanto toca.
class _EpisodeArt extends StatelessWidget {
  const _EpisodeArt({required this.theme, required this.playing});

  final PodcastTheme theme;
  final bool playing;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 400),
      width: 72,
      height: 72,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            theme.color.withOpacity(0.55),
            theme.color.withOpacity(0.2),
          ],
        ),
        border: Border.all(
          color: playing ? PodAiColors.yellow : PodAiColors.glassBorder,
          width: playing ? 2 : 1.2,
        ),
        boxShadow: [
          BoxShadow(
            color: (playing ? PodAiColors.yellow : theme.color)
                .withOpacity(0.45),
            blurRadius: playing ? 28 : 18,
          ),
        ],
      ),
      child: Icon(theme.icon, size: 34, color: Colors.white),
    );
  }
}

class _SegmentTile extends StatelessWidget {
  const _SegmentTile({
    required this.segment,
    required this.isCurrent,
    required this.accent,
  });

  final ScriptSegment segment;
  final bool isCurrent;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      margin: const EdgeInsets.symmetric(vertical: 3),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isCurrent
            ? PodAiColors.yellow.withOpacity(0.14)
            : Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isCurrent
              ? PodAiColors.yellow.withOpacity(0.7)
              : Colors.transparent,
          width: 1.2,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            switch (segment.kind) {
              SegmentKind.intro => Icons.mic_rounded,
              SegmentKind.news => Icons.article_rounded,
              SegmentKind.filler => Icons.info_rounded,
              SegmentKind.outro => Icons.waving_hand_rounded,
            },
            size: 18,
            color: isCurrent ? PodAiColors.yellow : PodAiColors.lavender,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              segment.text,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: isCurrent ? Colors.white : PodAiColors.onDarkMuted,
                    fontWeight:
                        isCurrent ? FontWeight.w600 : FontWeight.normal,
                    height: 1.4,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ArticleTile extends StatelessWidget {
  const _ArticleTile({required this.article});

  final NewsArticle article;

  Future<void> _open(BuildContext context) async {
    final uri = Uri.tryParse(article.link);
    if (uri == null) return;
    final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!ok && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Não foi possível abrir o link.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 8),
      leading: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: PodAiColors.violet.withOpacity(0.35),
          border: Border.all(color: PodAiColors.glassBorder),
        ),
        child: const Icon(Icons.newspaper_rounded, size: 18),
      ),
      title: Text(article.title,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontWeight: FontWeight.w600)),
      subtitle: Text(
        '${article.source} · ${article.relativeTime()}',
        style: const TextStyle(color: PodAiColors.lavender),
      ),
      trailing: const Icon(Icons.open_in_new_rounded,
          size: 18, color: PodAiColors.yellow),
      onTap: article.link.isEmpty ? null : () => _open(context),
    );
  }
}

class _Loading extends StatelessWidget {
  const _Loading({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: GlassPanel(
          strong: true,
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const PodAiMark(size: 64),
              const SizedBox(height: 20),
              const SizedBox(
                width: 28,
                height: 28,
                child: CircularProgressIndicator(strokeWidth: 3),
              ),
              const SizedBox(height: 16),
              Text(message,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              Text('Filtrando apenas as últimas 72 horas',
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: PodAiColors.lavender)),
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({super.key, required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: GlassPanel(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_rounded,
                  size: 52, color: PodAiColors.yellow),
              const SizedBox(height: 16),
              Text(message,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyLarge),
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Tentar novamente'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

