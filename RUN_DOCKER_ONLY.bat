@echo off
cd /d "%~dp0"
echo ========================================================
echo   A iniciar TODOS os contentores do Docker...
echo ========================================================
echo.

docker compose up -d

echo.
echo [OK] Todos os contentores definidos no docker-compose.yml estao a correr!
pause
