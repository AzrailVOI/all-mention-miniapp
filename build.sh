#!/bin/bash
# Скрипт только для компиляции (без запуска)
# Для Linux/Mac

set -e  # Остановка при ошибке

# Переходим в директорию, где находится скрипт
cd "$(dirname "$0")"

echo "========================================"
echo "Компиляция All Mention Mini App"
echo "========================================"
echo ""
echo "Текущая директория: $(pwd)"
echo ""

# Проверка наличия Node.js
if ! command -v node &> /dev/null; then
    echo "[ОШИБКА] Node.js не найден. Установите Node.js: https://nodejs.org/"
    exit 1
fi

echo "[1/2] Установка зависимостей Node.js..."
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
echo "[2/2] Компиляция TypeScript..."
npx tsc --project tsconfig.json
if [ $? -ne 0 ]; then
    echo "[ОШИБКА] Не удалось скомпилировать TypeScript"
    exit 1
fi
echo "TypeScript успешно скомпилирован!"

echo ""
echo "Готово! Теперь можно запустить приложение: python main.py"
