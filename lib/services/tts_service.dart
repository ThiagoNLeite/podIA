import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

enum PlaybackState { idle, playing, paused, completed }

/// Narra o roteiro usando o sintetizador de voz do próprio dispositivo.
///
/// O texto é falado parágrafo por parágrafo, o que permite pausar/retomar de
/// forma consistente em Android e iOS e exibir o progresso na interface.
class TtsService extends ChangeNotifier {
  TtsService() {
    _tts.setErrorHandler((message) {
      debugPrint('TTS erro: $message');
      _finish(PlaybackState.idle);
    });
  }

  final FlutterTts _tts = FlutterTts();

  List<String> _paragraphs = const [];
  int _index = 0;
  int _runId = 0;
  bool _initialized = false;

  PlaybackState _state = PlaybackState.idle;
  PlaybackState get state => _state;

  bool get isPlaying => _state == PlaybackState.playing;
  bool get isPaused => _state == PlaybackState.paused;

  /// Índice do parágrafo que está sendo falado (ou -1 quando parado).
  int get currentIndex =>
      _state == PlaybackState.idle || _state == PlaybackState.completed
          ? -1
          : _index;

  double get progress => _paragraphs.isEmpty
      ? 0
      : (_index / _paragraphs.length).clamp(0.0, 1.0).toDouble();

  /// Velocidade da fala no formato do flutter_tts (0.0–1.0; 0.5 é o normal).
  double _rate = 0.5;
  double get rate => _rate;

  double _pitch = 1.0;
  double get pitch => _pitch;

  /// Palavras por minuto aproximadas para a velocidade atual.
  /// Usado para estimar a duração do episódio.
  double get wordsPerMinute => 150 * (_rate / 0.5);

  Future<void> setRate(double value) async {
    _rate = value.clamp(0.2, 1.0).toDouble();
    if (_initialized) await _tts.setSpeechRate(_rate);
    notifyListeners();
  }

  Future<void> setPitch(double value) async {
    _pitch = value.clamp(0.5, 2.0).toDouble();
    if (_initialized) await _tts.setPitch(_pitch);
    notifyListeners();
  }

  Future<void> _ensureInitialized() async {
    if (_initialized) return;
    await _tts.setLanguage('pt-BR');
    await _tts.awaitSpeakCompletion(true);
    if (!kIsWeb && Platform.isIOS) {
      await _tts.setSharedInstance(true);
      await _tts.setIosAudioCategory(
        IosTextToSpeechAudioCategory.playback,
        [
          IosTextToSpeechAudioCategoryOptions.defaultToSpeaker,
          IosTextToSpeechAudioCategoryOptions.mixWithOthers,
        ],
        IosTextToSpeechAudioMode.spokenAudio,
      );
    }
    _initialized = true;
  }

  /// Verifica se há uma voz em português instalada no aparelho.
  Future<bool> hasPortugueseVoice() async {
    try {
      await _ensureInitialized();
      final result = await _tts.isLanguageAvailable('pt-BR');
      return result == true || result == 1;
    } catch (_) {
      return true; // Em caso de dúvida, deixa o sistema tentar.
    }
  }

  /// Começa a narrar do início.
  Future<void> play(List<String> paragraphs) async {
    await stop();
    _paragraphs = List.unmodifiable(paragraphs);
    _index = 0;
    await _run();
  }

  /// Retoma a partir do parágrafo em que parou.
  Future<void> resume() async {
    if (_state != PlaybackState.paused) return;
    await _run();
  }

  Future<void> pause() async {
    if (_state != PlaybackState.playing) return;
    _runId++;
    _state = PlaybackState.paused;
    notifyListeners();
    await _tts.stop();
  }

  Future<void> stop() async {
    _runId++;
    _index = 0;
    _state = PlaybackState.idle;
    notifyListeners();
    await _tts.stop();
  }

  Future<void> _run() async {
    await _ensureInitialized();
    await _tts.setSpeechRate(_rate);
    await _tts.setPitch(_pitch);

    final myRun = ++_runId;
    _state = PlaybackState.playing;
    notifyListeners();

    while (_index < _paragraphs.length && myRun == _runId) {
      notifyListeners();
      await _tts.speak(_paragraphs[_index]);
      if (myRun != _runId) return; // pausado ou parado durante a fala
      _index++;
    }

    if (myRun == _runId) {
      _index = 0;
      _finish(PlaybackState.completed);
    }
  }

  void _finish(PlaybackState newState) {
    _state = newState;
    notifyListeners();
  }

  @override
  void dispose() {
    _runId++;
    _tts.stop();
    super.dispose();
  }
}
