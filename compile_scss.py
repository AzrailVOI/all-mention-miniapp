#!/usr/bin/env python3
"""
Скрипт для компиляции SCSS в CSS
Использование:
    python compile_scss.py          # Компиляция один раз
    python compile_scss.py watch    # Отслеживание изменений
    python compile_scss.py compressed  # Компиляция в сжатом виде
"""
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webapp.utils.scss_compiler import compile_scss, watch_scss
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'watch':
        watch_scss()
    else:
        output_style = sys.argv[1] if len(sys.argv) > 1 else 'expanded'
        success = compile_scss(output_style=output_style)
        sys.exit(0 if success else 1)
