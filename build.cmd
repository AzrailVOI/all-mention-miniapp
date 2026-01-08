@echo off
REM Скрипт только для компиляции (без запуска)
REM Для Windows

REM Переходим в директорию, где находится скрипт
cd /d "%~dp0"

echo ========================================
echo Компиляция All Mention Mini App
echo ========================================
echo.
echo Текущая директория: %CD%
echo.

REM Проверка наличия Node.js
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Node.js не найден. Установите Node.js: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/2] Установка зависимостей Node.js...
if not exist "node_modules" (
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ОШИБКА] Не удалось установить зависимости Node.js
        pause
        exit /b 1
    )
) else (
    echo Зависимости Node.js уже установлены
)

echo.
echo [2/2] Компиляция TypeScript...
call npx tsc --project tsconfig.json
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Не удалось скомпилировать TypeScript
    pause
    exit /b 1
)
echo TypeScript успешно скомпилирован!

echo.
echo Готово! Теперь можно запустить приложение: python main.py
pause
