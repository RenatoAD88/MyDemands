@echo off
setlocal

if not exist .venv\Scripts\python.exe (
  echo [ERRO] Ambiente virtual .venv nao encontrado.
  exit /b 1
)

set "PY=.venv\Scripts\python.exe"

%PY% -m pip install --upgrade pip || exit /b 1
%PY% -m pip install -r requirements.txt || exit /b 1
%PY% -m pip install --upgrade pyinstaller || exit /b 1

%PY% -m PyInstaller --noconfirm --clean DemandasApp.spec || exit /b 1

if not exist dist\DemandasApp.exe (
  echo [ERRO] Executavel nao encontrado em dist\DemandasApp.exe
  exit /b 1
)

dist\DemandasApp.exe --self-test-crypto
if errorlevel 1 (
  echo [ERRO] Self-test falhou.
  exit /b 1
)

echo [OK] Build e smoke test concluidos.
exit /b 0
