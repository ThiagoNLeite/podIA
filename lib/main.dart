import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:provider/provider.dart';

import 'screens/home_screen.dart';
import 'services/app_settings.dart';
import 'services/tts_service.dart';
import 'theme/app_theme.dart';
import 'widgets/glass.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('pt_BR');

  // Barra de status transparente, para o gradiente roxo ocupar a tela toda.
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    statusBarBrightness: Brightness.dark,
    systemNavigationBarColor: PodAiColors.deepPurple,
    systemNavigationBarIconBrightness: Brightness.light,
  ));
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);

  final settings = AppSettings();
  await settings.load();

  final tts = TtsService();
  await tts.setRate(settings.speechRate);
  await tts.setPitch(settings.pitch);

  runApp(PodAiApp(settings: settings, tts: tts));
}

class PodAiApp extends StatelessWidget {
  const PodAiApp({super.key, required this.settings, required this.tts});

  final AppSettings settings;
  final TtsService tts;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AppSettings>.value(value: settings),
        ChangeNotifierProvider<TtsService>.value(value: tts),
      ],
      child: MaterialApp(
        title: 'PodAI',
        debugShowCheckedModeBanner: false,
        locale: const Locale('pt', 'BR'),
        supportedLocales: const [Locale('pt', 'BR')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: PodAiTheme.build(),
        darkTheme: PodAiTheme.build(),
        themeMode: ThemeMode.dark,
        // O fundo fica fora do Navigator, então persiste entre as telas e as
        // transições de rota acontecem "sobre o vidro".
        builder: (context, child) =>
            PodAiBackground(child: child ?? const SizedBox.shrink()),
        home: const HomeScreen(),
      ),
    );
  }
}
