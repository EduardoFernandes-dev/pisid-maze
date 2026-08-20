@echo off
cd /d "%~dp0"
:: ==========================================
:: PC1: MongoDB + Mosquitto + Mazerun + Script 1
:: ==========================================
if "%~1" neq "MAX" (
    start /max "" "%~dpnx0" MAX
    exit
)

echo ==========================================
echo    PC1: A INICIAR O AMBIENTE
echo ==========================================
echo.

echo [*] A limpar ficheiros antigos (.pkl, .csv, .log)...
del /q /s /f ".\*.pkl" >nul 2>&1
del /q /s /f ".\*.csv" >nul 2>&1
del /q /s /f ".\*.log" >nul 2>&1
echo [OK] Limpeza concluida.
echo.

echo [1/3] A verificar e iniciar o Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
:esperar_docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto esperar_docker
)
echo [OK] O Docker esta pronto!
echo.

echo [2/3] A iniciar MongoDB + Mosquitto (docker-compose-pc1.yml)...
docker compose -f docker-compose-pc1.yml up -d
echo.

echo [*] A aguardar 15 segundos para os servicos iniciarem...
timeout /t 15 /nobreak >nul
echo.

echo [3/3] A abrir terminais (Mazerun + Script 1 + Script 2)...
wt -M new-tab -d ".\ficheiros_auxiliares\mazerun" --title "Mazerun EXE" cmd /k "mazerun.exe --flagMessage 1 --delay 10 --broker broker.mqtt-dashboard.com --portbroker 1883 16" ; split-pane -V -d . --title "Script 1 (MongoDB)" cmd /k "python .\ficheiros_auxiliares\script_1_mongodb.py" ; split-pane -H -d . --title "Script 2 (Mongo->MQTT)" cmd /k "python .\ficheiros_auxiliares\script_2_mongo_to_mqtt.py"

echo.
echo ==========================================
echo    PC1: TODOS OS PROCESSOS INICIADOS!
echo ==========================================
timeout /t 3 /nobreak >nul
exit
