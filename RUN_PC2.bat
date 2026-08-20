@echo off
cd /d "%~dp0"
:: ==========================================
:: PC2: MySQL + phpMyAdmin + PHP + Script 2
:: ==========================================
if "%~1" neq "MAX" (
    start /max "" "%~dpnx0" MAX
    exit
)

echo ==========================================
echo    PC2: A INICIAR O AMBIENTE
echo ==========================================
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

echo [2/3] A iniciar MySQL + phpMyAdmin + PHP (docker-compose-pc2.yml)...
docker compose -f docker-compose-pc2.yml up -d
echo.

echo [*] A aguardar 30 segundos para o MySQL iniciar...
timeout /t 30 /nobreak >nul
echo.

echo [3/4] A criar/atualizar Stored Procedures no MySQL...
docker exec -i pisid_mysql mysql -uroot -proot pisid_maze < .\mysql-init\02_stored_procedures.sql
docker exec -i pisid_mysql mysql -uroot -proot pisid_maze < .\mysql-init\04_form_procedures.sql
if %errorlevel% equ 0 (
    echo [OK] Stored Procedures criadas com sucesso!
) else (
    echo [!] AVISO: Falha ao criar SPs. Verifique se o MySQL esta pronto.
)
echo.

echo [4/4] A abrir terminais do Script 3 e Jogador...
wt -M new-tab -d . --title "Script 3 (MySQL)" cmd /k "python .\ficheiros_auxiliares\script_3_mysql_monitor.py" ; split-pane -V -d . --title "Jogador" cmd /k "python .\ficheiros_auxiliares\jogador.py"

echo.
echo ==========================================
echo    PC2: TODOS OS PROCESSOS INICIADOS!
echo    phpMyAdmin: http://localhost:8080
echo ==========================================
timeout /t 3 /nobreak >nul
exit
