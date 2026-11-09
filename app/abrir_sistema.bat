@echo off
rem Abre o sistema de gestao LocaMaq no computador. Duplo clique neste arquivo.
rem Fechar esta janela desliga o sistema.
chcp 65001 >nul
title LocaMaq Gestao - servidor local
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Preparando o ambiente Python, so na primeira vez...
  python -m venv .venv || goto erro
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto erro
)
set "PY=.venv\Scripts\python.exe"

"%PY%" manage.py migrate --noinput || goto erro
"%PY%" manage.py criar_perfis >nul || goto erro
"%PY%" manage.py importar_base --se-vazio || goto erro

"%PY%" manage.py checar_admin
if errorlevel 1 (
  echo.
  echo ============================================================
  echo  Crie o seu usuario administrador.
  echo  A senha nao aparece enquanto voce digita: e normal.
  echo ============================================================
  "%PY%" manage.py createsuperuser || goto erro
  "%PY%" manage.py checar_admin >nul || goto erro
)

echo.
echo Sistema no ar: http://127.0.0.1:8000
echo Para desligar, feche esta janela.
start "" cmd /c "timeout /t 4 >nul & start http://127.0.0.1:8000/"
"%PY%" manage.py runserver 127.0.0.1:8000
goto fim

:erro
echo.
echo Algo deu errado. Leia a mensagem acima e mande para o Claude.
pause
:fim
