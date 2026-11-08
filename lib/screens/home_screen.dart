import 'package:flutter/material.dart';

import '../data/themes.dart';
import '../models/podcast_theme.dart';
import '../theme/app_theme.dart';
import '../widgets/glass.dart';
import '../widgets/podai_logo.dart';
import 'podcast_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Scaffold(
      backgroundColor: Colors.transparent,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const PodAiLogo(size: 34),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: GlassIconButton(
              tooltip: 'Configurações',
              icon: Icons.tune_rounded,
              size: 42,
              iconSize: 20,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                    builder: (_) => const SettingsScreen()),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: GlassPanel(
                strong: true,
                padding: const EdgeInsets.all(18),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Suas notícias,\nem áudio.',
                            style: textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.w800,
                              height: 1.1,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Escolha um tema e o PodAI monta um episódio de '
                            '~2 minutos só com notícias das últimas 72 horas.',
                            style: textTheme.bodySmall?.copyWith(
                              color: PodAiColors.lavender,
                            ),
                          ),
                          const SizedBox(height: 12),
                          const Wrap(
                            spacing: 8,
                            runSpacing: 6,
                            children: [
                              GlassChip(
                                  icon: Icons.timer_outlined, label: '~2 min'),
                              GlassChip(
                                  icon: Icons.schedule_rounded,
                                  label: 'últimas 72h'),
                              GlassChip(
                                  icon: Icons.auto_awesome, label: '6 temas'),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    const PodAiMark(size: 72),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 4),
              child: Text(
                'Temas',
                style: textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: PodAiColors.lightYellow,
                  letterSpacing: 0.4,
                ),
              ),
            ),
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final columns = constraints.maxWidth > 600 ? 3 : 2;
                  return GridView.builder(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                    gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: columns,
                      mainAxisSpacing: 14,
                      crossAxisSpacing: 14,
                      childAspectRatio: 0.92,
                    ),
                    itemCount: kPodcastThemes.length,
                    itemBuilder: (context, index) =>
                        _ThemeCard(theme: kPodcastThemes[index]),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ThemeCard extends StatelessWidget {
  const _ThemeCard({required this.theme});

  final PodcastTheme theme;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return GlassPanel(
      tint: theme.color,
      padding: const EdgeInsets.all(16),
      borderColor: theme.color.withOpacity(0.45),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute<void>(builder: (_) => PodcastScreen(theme: theme)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: theme.color.withOpacity(0.22),
              border: Border.all(color: theme.color.withOpacity(0.6)),
              boxShadow: [
                BoxShadow(
                  color: theme.color.withOpacity(0.35),
                  blurRadius: 18,
                ),
              ],
            ),
            child: Icon(theme.icon, size: 24, color: Colors.white),
          ),
          const Spacer(),
          Text(
            theme.name,
            style: textTheme.titleMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            theme.description,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: textTheme.bodySmall?.copyWith(color: PodAiColors.lavender),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(Icons.play_circle_fill_rounded,
                  size: 18, color: PodAiColors.yellow),
              const SizedBox(width: 6),
              Text(
                'Ouvir episódio',
                style: textTheme.labelSmall?.copyWith(
                  color: PodAiColors.lightYellow,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
