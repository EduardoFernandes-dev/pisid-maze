@echo off
cd /d "%~dp0"
:: ==========================================
:: TRUQUE 1: Auto-Maximizar a Primeira Consola
:: ==========================================
if "%~1" neq "MAX" (
    start /max "" "%~dpnx0" MAX
    exit
)

echo ==========================================
echo    A INICIAR O AMBIENTE COMPLETO
echo ==========================================
echo.
echo [*] A limpar ficheiros antigos (.pkl, .csv, .log) de todas as diretorias...
:: Removido o "if exist" para garantir que a procura entra sempre nas subpastas!
del /q /s /f ".\*.pkl" >nul 2>&1
del /q /s /f ".\*.csv" >nul 2>&1
del /q /s /f ".\*.log" >nul 2>&1
echo [OK] Limpeza concluida com sucesso! O ambiente esta fresco.
echo.

echo [1/3] A verificar e iniciar o Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
:esperar_docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto esperar_docker
)
echo [OK] O Docker esta pronto e a correr!
echo.

echo [2/3] A iniciar as imagens Docker do projeto (docker compose)...
docker compose up -d
echo.

echo [*] A aguardar 30 segundos para as bases de dados e broker iniciarem corretamente...
timeout /t 30 /nobreak >nul
echo.

echo ========================================================
echo   A criar/atualizar Stored Procedures no MySQL...
echo ========================================================
docker exec -i pisid_mysql mysql -uroot -proot pisid_maze < .\mysql-init\02_stored_procedures.sql
docker exec -i pisid_mysql mysql -uroot -proot pisid_maze < .\mysql-init\04_form_procedures.sql
echo.

echo ========================================================
echo   [Script 0] A extrair SetupMaze e Mapa da Nuvem...
echo ========================================================
python ficheiros_auxiliares\script_0_setup.py
echo ========================================================
echo.

echo [3/3] A abrir terminais em Split Screen (Mazerun, Script 1, Script 2, Script 3 e Jogador)...
wt -M new-tab -d ".\ficheiros_auxiliares\mazerun" --title "Mazerun EXE" cmd /k "mazerun.exe --flagMessage 1 --delay 10 --broker broker.mqtt-dashboard.com --portbroker 1883 16" ; split-pane -V -d . --title "Script 1 (MongoDB)" cmd /k "python .\ficheiros_auxiliares\script_1_mongodb.py" ; split-pane -H -d . --title "Script 2 (Mongo MQTT)" cmd /k "python .\ficheiros_auxiliares\script_2_mongo_to_mqtt.py" ; split-pane -V -d . --title "Script 3 (MySQL)" cmd /k "python .\ficheiros_auxiliares\script_3_mysql_monitor.py" ; split-pane -H -d . --title "Jogador" cmd /k "python .\ficheiros_auxiliares\jogador.py"

echo.
echo ==========================================
echo    TODOS OS PROCESSOS FORAM INICIADOS!
echo ==========================================
timeout /t 3 /nobreak >nul
exit