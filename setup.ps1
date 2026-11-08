# Prepara o projeto na primeira vez (Windows / PowerShell).
# Gera as pastas nativas (android/, ios/) sem sobrescrever o código em lib/,
# baixa as dependências e roda os testes.
#
# Uso:  .\setup.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    Write-Error 'Flutter não encontrado no PATH. Instale em https://docs.flutter.dev/get-started/install'
}

flutter create . --platforms=android,ios --project-name news_podcast_app --org br.com.podai
flutter pub get
# Gera os ícones de launcher (Android e iOS) a partir de assets/icon/podai_icon.png
dart run flutter_launcher_icons
flutter test
Write-Host ''
Write-Host 'Pronto! Conecte um aparelho (ou abra um emulador) e execute:  flutter run' -ForegroundColor Green
