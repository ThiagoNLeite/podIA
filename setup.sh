#!/usr/bin/env bash
# Prepara o projeto na primeira vez (macOS / Linux).
# Gera as pastas nativas (android/, ios/) sem sobrescrever o código em lib/,
# baixa as dependências e roda os testes.
#
# Uso:  chmod +x setup.sh && ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v flutter >/dev/null 2>&1; then
  echo "Flutter não encontrado no PATH. Instale em https://docs.flutter.dev/get-started/install" >&2
  exit 1
fi

flutter create . --platforms=android,ios --project-name news_podcast_app --org br.com.podai
flutter pub get
# Gera os ícones de launcher (Android e iOS) a partir de assets/icon/podai_icon.png
dart run flutter_launcher_icons
flutter test
echo
echo "Pronto! Conecte um aparelho (ou abra um emulador) e execute:  flutter run"
