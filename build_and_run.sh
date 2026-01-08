#!/bin/bash
# Скрипт для компиляции TypeScript и SCSS, и запуска приложения
# Для Linux/Mac

set -e  # Остановка при ошибке

# Переходим в директорию, где находится скрипт
cd "$(dirname "$0")"

echo "========================================"
echo "Компиляция и запуск All Mention Mini App"
echo "========================================"
echo ""
echo "Текущая директория: $(pwd)"
echo ""

# Проверка наличия Node.js
if ! command -v node &> /dev/null; then
    echo "[ОШИБКА] Node.js не найден. Установите Node.js: https://nodejs.org/"
    exit 1
fi

# Проверка наличия Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ОШИБКА] Python не найден. Установите Python: https://www.python.org/"
    exit 1
fi

# Определяем команду Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "[1/3] Установка зависимостей Node.js..."
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo "[ОШИБКА] Не удалось установить зависимости Node.js"
        exit 1
    fi
else
    echo "Зависимости Node.js уже установлены"
fi

echo ""
echo "[2/3] Компиляция TypeScript..."
npx tsc --project tsconfig.json
if [ $? -ne 0 ]; then
    echo "[ОШИБКА] Не удалось скомпилировать TypeScript"
    exit 1
fi
echo "TypeScript успешно скомпилирован!"

echo ""
echo "[3/3] Запуск Flask приложения..."
echo ""
$PYTHON_CMD main.py
