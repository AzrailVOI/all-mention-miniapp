@echo off
REM Скрипт для компиляции TypeScript и SCSS, и запуска приложения
REM Для Windows

REM Переходим в директорию, где находится скрипт
cd /d "%~dp0"

echo ========================================
echo Компиляция и запуск All Mention Mini App
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

REM Проверка наличия Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Python не найден. Установите Python: https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Установка зависимостей Node.js...
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
echo [2/3] Компиляция TypeScript...
call npx tsc --project tsconfig.json
if %ERRORLEVEL% NEQ 0 (
    echo [ОШИБКА] Не удалось скомпилировать TypeScript
    pause
    exit /b 1
)
echo TypeScript успешно скомпилирован!

echo.
echo [3/3] Запуск Flask приложения...
echo.
python main.py

pause
