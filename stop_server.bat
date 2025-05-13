@echo off
taskkill /f /im "gestao-simples.exe"
if %errorlevel% equ 0 (
    echo Processo encerrado com sucesso. Fechando em 3 segundos...
) else (
    echo Nenhum processo encontrado. Fechando em 3 segundos...
)
timeout /t 3 /nobreak >nul