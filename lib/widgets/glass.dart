import 'dart:ui';

import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Fundo com gradiente roxo e "bolhas" de luz desfocadas, dando a sensação
/// de profundidade por trás dos painéis de vidro.
class PodAiBackground extends StatelessWidget {
  const PodAiBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(gradient: PodAiColors.background),
      child: Stack(
        children: [
          const Positioned(
            top: -80,
            right: -60,
            child: _Blob(color: PodAiColors.violet, size: 260),
          ),
          const Positioned(
            top: 220,
            left: -110,
            child: _Blob(color: PodAiColors.yellow, size: 220, opacity: 0.35),
          ),
          const Positioned(
            bottom: -120,
            right: -40,
            child: _Blob(color: PodAiColors.amber, size: 280, opacity: 0.25),
          ),
          Positioned.fill(child: child),
        ],
      ),
    );
  }
}

class _Blob extends StatelessWidget {
  const _Blob({required this.color, required this.size, this.opacity = 0.55});

  final Color color;
  final double size;
  final double opacity;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: ImageFiltered(
        imageFilter: ImageFilter.blur(sigmaX: 60, sigmaY: 60),
        child: Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: color.withOpacity(opacity),
          ),
        ),
      ),
    );
  }
}

/// Painel de vidro translúcido (liquid glass): desfoque do fundo, preenchimento
/// semitransparente, borda luminosa e um reflexo suave no topo.
class GlassPanel extends StatelessWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.borderRadius = 24,
    this.blur = 18,
    this.tint,
    this.strong = false,
    this.borderColor,
    this.onTap,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final double blur;

  /// Cor de tingimento adicional (ex.: a cor do tema).
  final Color? tint;

  /// Vidro mais opaco (para painéis de destaque).
  final bool strong;
  final Color? borderColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(borderRadius);
    final fill = strong ? PodAiColors.glassFillStrong : PodAiColors.glassFill;
    // Parte inferior um pouco mais transparente, para o vidro parecer "líquido".
    final fillBottom = Colors.white.withOpacity(strong ? 0.12 : 0.07);

    Widget content = Stack(
      children: [
        // Reflexo "líquido" no topo do painel.
        Positioned(
          top: 0,
          left: 0,
          right: 0,
          height: 60,
          child: IgnorePointer(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.white.withOpacity(0.18),
                    Colors.white.withOpacity(0.0),
                  ],
                ),
              ),
            ),
          ),
        ),
        Padding(padding: padding, child: child),
      ],
    );

    if (onTap != null) {
      content = Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: onTap,
          borderRadius: radius,
          splashColor: PodAiColors.yellow.withOpacity(0.15),
          highlightColor: Colors.white.withOpacity(0.05),
          child: content,
        ),
      );
    }

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: radius,
        boxShadow: const [
          BoxShadow(
            color: PodAiColors.glassShadow,
            blurRadius: 24,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: radius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: DecoratedBox(
            decoration: BoxDecoration(
              borderRadius: radius,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color.alphaBlend(tint?.withOpacity(0.28) ?? Colors.transparent,
                      fill),
                  Color.alphaBlend(tint?.withOpacity(0.10) ?? Colors.transparent,
                      fillBottom),
                ],
              ),
              border: Border.all(
                color: borderColor ?? PodAiColors.glassBorder,
                width: 1.2,
              ),
            ),
            child: content,
          ),
        ),
      ),
    );
  }
}

/// Botão circular de vidro (controles do player).
class GlassIconButton extends StatelessWidget {
  const GlassIconButton({
    super.key,
    required this.icon,
    required this.onPressed,
    this.tooltip,
    this.size = 52,
    this.iconSize = 26,
    this.primary = false,
  });

  final IconData icon;
  final VoidCallback? onPressed;
  final String? tooltip;
  final double size;
  final double iconSize;

  /// Botão principal: preenchido com o gradiente amarelo.
  final bool primary;

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null;
    final button = ClipOval(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Material(
          type: MaterialType.transparency,
          child: InkWell(
            onTap: onPressed,
            customBorder: const CircleBorder(),
            child: Ink(
              width: size,
              height: size,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: primary ? PodAiColors.accent : null,
                color: primary
                    ? null
                    : PodAiColors.glassFillStrong
                        .withOpacity(enabled ? 0.2 : 0.08),
                border: Border.all(
                  color: primary
                      ? PodAiColors.lightYellow.withOpacity(0.8)
                      : PodAiColors.glassBorder,
                  width: 1.2,
                ),
                boxShadow: primary
                    ? [
                        BoxShadow(
                          color: PodAiColors.yellow.withOpacity(0.45),
                          blurRadius: 24,
                          spreadRadius: 1,
                        ),
                      ]
                    : null,
              ),
              child: Icon(
                icon,
                size: iconSize,
                color: primary
                    ? PodAiColors.deepPurple
                    : Colors.white.withOpacity(enabled ? 1 : 0.35),
              ),
            ),
          ),
        ),
      ),
    );
    return tooltip == null ? button : Tooltip(message: tooltip!, child: button);
  }
}

/// Etiqueta pequena em amarelo (ex.: "~2 min · 72h").
class GlassChip extends StatelessWidget {
  const GlassChip({super.key, required this.label, this.icon});

  final String label;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: PodAiColors.yellow.withOpacity(0.16),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: PodAiColors.yellow.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 13, color: PodAiColors.lightYellow),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: PodAiColors.lightYellow,
                  fontWeight: FontWeight.w600,
                ),
          ),
        ],
      ),
    );
  }
}
