import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/app_settings.dart';
import '../services/tts_service.dart';
import '../theme/app_theme.dart';
import '../widgets/glass.dart';
import '../widgets/podai_logo.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _apiKeyController;
  bool _obscureKey = true;

  @override
  void initState() {
    super.initState();
    _apiKeyController =
        TextEditingController(text: context.read<AppSettings>().openAiApiKey);
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<AppSettings>();
    final tts = context.read<TtsService>();
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: const Text('Configurações')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
        children: [
          _SectionTitle('Narração', icon: Icons.graphic_eq_rounded),
          GlassPanel(
            child: Column(
              children: [
                _SliderRow(
                  label: 'Velocidade da voz',
                  valueLabel: _rateLabel(settings.speechRate),
                  slider: Slider(
                    value: settings.speechRate,
                    min: 0.3,
                    max: 0.8,
                    divisions: 10,
                    label: _rateLabel(settings.speechRate),
                    onChanged: (v) {
                      settings.setSpeechRate(v);
                      tts.setRate(v);
                    },
                  ),
                ),
                _SliderRow(
                  label: 'Tom da voz',
                  valueLabel: settings.pitch.toStringAsFixed(1),
                  slider: Slider(
                    value: settings.pitch,
                    min: 0.7,
                    max: 1.4,
                    divisions: 7,
                    label: settings.pitch.toStringAsFixed(1),
                    onChanged: (v) {
                      settings.setPitch(v);
                      tts.setPitch(v);
                    },
                  ),
                ),
                const SizedBox(height: 4),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    icon: const Icon(Icons.record_voice_over_rounded),
                    label: const Text('Testar voz'),
                    onPressed: () => tts.play(const [
                      'Olá! Eu sou a voz do PodAI, e vou narrar o seu podcast de notícias.',
                    ]),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _SectionTitle('Roteiro com IA (opcional)',
              icon: Icons.auto_awesome),
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Por padrão o roteiro é montado no próprio aparelho, sem custo. '
                  'Se preferir um texto mais natural, informe uma chave de API '
                  'compatível com OpenAI. A chave fica salva apenas neste dispositivo.',
                  style:
                      textTheme.bodySmall?.copyWith(color: PodAiColors.lavender),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: _apiKeyController,
                  obscureText: _obscureKey,
                  autocorrect: false,
                  enableSuggestions: false,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    labelText: 'Chave da API (sk-...)',
                    prefixIcon: const Icon(Icons.key_rounded,
                        color: PodAiColors.lavender),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscureKey
                            ? Icons.visibility_rounded
                            : Icons.visibility_off_rounded,
                        color: PodAiColors.lavender,
                      ),
                      onPressed: () =>
                          setState(() => _obscureKey = !_obscureKey),
                    ),
                  ),
                  onChanged: settings.setOpenAiApiKey,
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Usar IA para escrever o roteiro'),
                  subtitle: settings.openAiApiKey.isEmpty
                      ? const Text('Informe uma chave para ativar',
                          style: TextStyle(color: PodAiColors.lavender))
                      : null,
                  value: settings.useAiToggle &&
                      settings.openAiApiKey.isNotEmpty,
                  onChanged: settings.openAiApiKey.isEmpty
                      ? null
                      : (v) => settings.setUseAi(v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _SectionTitle('Sobre', icon: Icons.info_outline_rounded),
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    PodAiLogo(size: 36),
                    Spacer(),
                    GlassChip(label: 'v1.0'),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'As notícias vêm do feed público do Google Notícias (pt-BR). '
                  'Apenas itens publicados nas últimas 72 horas são usados; '
                  'cada episódio é dimensionado para cerca de 2 minutos de '
                  'narração.',
                  style:
                      textTheme.bodySmall?.copyWith(color: PodAiColors.lavender),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static String _rateLabel(double rate) {
    if (rate < 0.4) return 'Lenta';
    if (rate < 0.55) return 'Normal';
    if (rate < 0.7) return 'Rápida';
    return 'Muito rápida';
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.title, {required this.icon});

  final String title;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 0, 4, 10),
      child: Row(
        children: [
          Icon(icon, size: 18, color: PodAiColors.yellow),
          const SizedBox(width: 8),
          Text(
            title,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: PodAiColors.lightYellow,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.4,
                ),
          ),
        ],
      ),
    );
  }
}

class _SliderRow extends StatelessWidget {
  const _SliderRow({
    required this.label,
    required this.valueLabel,
    required this.slider,
  });

  final String label;
  final String valueLabel;
  final Widget slider;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: Text(label)),
            GlassChip(label: valueLabel),
          ],
        ),
        slider,
      ],
    );
  }
}
