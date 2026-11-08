import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Preferências persistidas do usuário.
class AppSettings extends ChangeNotifier {
  static const _keyRate = 'speech_rate';
  static const _keyPitch = 'speech_pitch';
  static const _keyApiKey = 'openai_api_key';
  static const _keyUseAi = 'use_ai';

  SharedPreferences? _prefs;

  double _speechRate = 0.5;
  double get speechRate => _speechRate;

  double _pitch = 1.0;
  double get pitch => _pitch;

  String _openAiApiKey = '';
  String get openAiApiKey => _openAiApiKey;

  bool _useAi = false;
  bool get useAi => _useAi && _openAiApiKey.isNotEmpty;
  bool get useAiToggle => _useAi;

  Future<void> load() async {
    _prefs = await SharedPreferences.getInstance();
    _speechRate = _prefs!.getDouble(_keyRate) ?? 0.5;
    _pitch = _prefs!.getDouble(_keyPitch) ?? 1.0;
    _openAiApiKey = _prefs!.getString(_keyApiKey) ?? '';
    _useAi = _prefs!.getBool(_keyUseAi) ?? false;
    notifyListeners();
  }

  Future<void> setSpeechRate(double value) async {
    _speechRate = value;
    await _prefs?.setDouble(_keyRate, value);
    notifyListeners();
  }

  Future<void> setPitch(double value) async {
    _pitch = value;
    await _prefs?.setDouble(_keyPitch, value);
    notifyListeners();
  }

  Future<void> setOpenAiApiKey(String value) async {
    _openAiApiKey = value.trim();
    await _prefs?.setString(_keyApiKey, _openAiApiKey);
    notifyListeners();
  }

  Future<void> setUseAi(bool value) async {
    _useAi = value;
    await _prefs?.setBool(_keyUseAi, value);
    notifyListeners();
  }
}
