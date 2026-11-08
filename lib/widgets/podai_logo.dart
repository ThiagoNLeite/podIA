import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Logotipo do PodAI: ícone de microfone em vidro + wordmark
/// ("Pod" em branco, "AI" em gradiente amarelo).
class PodAiLogo extends StatelessWidget {
  const PodAiLogo({super.key, this.size = 40, this.showWordmark = true});

  final double size;
  final bool showWordmark;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        PodAiMark(size: size),
        if (showWordmark) ...[
          SizedBox(width: size * 0.3),
          PodAiWordmark(fontSize: size * 0.7),
        ],
      ],
    );
  }
}

/// Apenas o símbolo (quadrado arredondado roxo com microfone e faísca amarela).
class PodAiMark extends StatelessWidget {
  const PodAiMark({super.key, this.size = 40});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(size * 0.28),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [PodAiColors.violet, PodAiColors.purple],
        ),
        border: Border.all(color: PodAiColors.glassBorder, width: 1),
        boxShadow: [
          BoxShadow(
            color: PodAiColors.violet.withOpacity(0.5),
            blurRadius: size * 0.4,
            offset: Offset(0, size * 0.15),
          ),
        ],
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Icon(Icons.mic_rounded,
              size: size * 0.58, color: Colors.white.withOpacity(0.95)),
          Positioned(
            top: size * 0.14,
            right: size * 0.16,
            child: Icon(Icons.auto_awesome,
                size: size * 0.24, color: PodAiColors.yellow),
          ),
        ],
      ),
    );
  }
}

/// Wordmark "PodAI".
class PodAiWordmark extends StatelessWidget {
  const PodAiWordmark({super.key, this.fontSize = 28});

  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(
      fontSize: fontSize,
      fontWeight: FontWeight.w800,
      letterSpacing: -0.5,
      height: 1,
    );
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.baseline,
      textBaseline: TextBaseline.alphabetic,
      children: [
        Text('Pod', style: style.copyWith(color: Colors.white)),
        ShaderMask(
          shaderCallback: (bounds) => PodAiColors.accent.createShader(bounds),
          blendMode: BlendMode.srcIn,
          child: Text('AI', style: style.copyWith(color: Colors.white)),
        ),
      ],
    );
  }
}
