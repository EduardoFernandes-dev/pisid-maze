@echo off
echo ========================================================
echo   A iniciar Servidor Web (PHP Nativo) na porta 8000...
echo ========================================================
echo O servidor estah a correr localmente (sem Docker).
echo.
echo 1. Va ao seu browser e abra: http://localhost:8000
echo 2. Mantenha esta janela preta aberta enquanto usar o site.
echo.
.\PISID-Edu-updated\PISID-Edu-updated\php-local\php.exe -S localhost:8000 -t html
pause
