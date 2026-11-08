import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

/// Paleta oficial do PodAI: roxo profundo + amarelo vibrante.
abstract final class PodAiColors {
  // Roxos
  static const Color deepPurple = Color(0xFF2E1065); // fundo mais escuro
  static const Color purple = Color(0xFF5B21B6); // roxo base
  static const Color violet = Color(0xFF7C3AED); // roxo vivo
  static const Color lavender = Color(0xFFC4B5FD); // texto secundário

  // Amarelos
  static const Color yellow = Color(0xFFFACC15); // destaque principal
  static const Color lightYellow = Color(0xFFFDE68A); // destaque suave
  static const Color amber = Color(0xFFF59E0B); // amarelo quente

  // Superfícies
  static const Color onDark = Colors.white;
  static const Color onDarkMuted = Color(0xDDFFFFFF);
  static const Color glassFill = Color(0x1FFFFFFF);
  static const Color glassFillStrong = Color(0x33FFFFFF);
  static const Color glassBorder = Color(0x55FFFFFF);
  static const Color glassShadow = Color(0x55000000);

  /// Gradiente de fundo usado em todas as telas.
  static const LinearGradient background = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF1E0A47), deepPurple, purple],
    stops: [0.0, 0.55, 1.0],
  );

  /// Gradiente de destaque (botões, logo).
  static const LinearGradient accent = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [lightYellow, yellow, amber],
  );
}

/// ThemeData do PodAI (sempre escuro, para valorizar o efeito de vidro).
abstract final class PodAiTheme {
  static ThemeData build() {
    final scheme = ColorScheme.fromSeed(
      seedColor: PodAiColors.violet,
      brightness: Brightness.dark,
    ).copyWith(
      primary: PodAiColors.yellow,
      onPrimary: PodAiColors.deepPurple,
      primaryContainer: PodAiColors.violet,
      onPrimaryContainer: Colors.white,
      secondary: PodAiColors.lavender,
      onSecondary: PodAiColors.deepPurple,
      tertiary: PodAiColors.amber,
      surface: PodAiColors.deepPurple,
      onSurface: Colors.white,
      onSurfaceVariant: PodAiColors.lavender,
      outline: PodAiColors.glassBorder,
      error: const Color(0xFFFF8A80),
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: Colors.transparent,
      canvasColor: Colors.transparent,
    );

    return base.copyWith(
      // Transições suaves: o fundo roxo é compartilhado entre as telas.
      pageTransitionsTheme: const PageTransitionsTheme(builders: {
        TargetPlatform.android: FadeUpwardsPageTransitionsBuilder(),
        TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
      }),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: Colors.white,
          letterSpacing: -0.3,
        ),
      ),
      textTheme: base.textTheme.apply(
        bodyColor: Colors.white,
        displayColor: Colors.white,
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: PodAiColors.yellow,
        inactiveTrackColor: PodAiColors.glassFillStrong,
        thumbColor: PodAiColors.yellow,
        overlayColor: PodAiColors.yellow.withOpacity(0.2),
        valueIndicatorColor: PodAiColors.yellow,
        valueIndicatorTextStyle:
            const TextStyle(color: PodAiColors.deepPurple),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected)
                ? PodAiColors.deepPurple
                : PodAiColors.lavender),
        trackColor: WidgetStateProperty.resolveWith((states) =>
            states.contains(WidgetState.selected)
                ? PodAiColors.yellow
                : PodAiColors.glassFillStrong),
        trackOutlineColor:
            const WidgetStatePropertyAll(PodAiColors.glassBorder),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: PodAiColors.glassFill,
        labelStyle: const TextStyle(color: PodAiColors.lavender),
        hintStyle: const TextStyle(color: PodAiColors.lavender),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: PodAiColors.glassBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: PodAiColors.glassBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: PodAiColors.yellow, width: 1.5),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: PodAiColors.yellow,
          foregroundColor: PodAiColors.deepPurple,
          textStyle: const TextStyle(fontWeight: FontWeight.w700),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: PodAiColors.violet,
        contentTextStyle: const TextStyle(color: Colors.white),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: PodAiColors.glassBorder),
        ),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: PodAiColors.yellow,
      ),
      dividerTheme: const DividerThemeData(color: PodAiColors.glassBorder),
      listTileTheme: const ListTileThemeData(
        iconColor: PodAiColors.lavender,
        textColor: Colors.white,
      ),
      iconTheme: const IconThemeData(color: Colors.white),
    );
  }
}
