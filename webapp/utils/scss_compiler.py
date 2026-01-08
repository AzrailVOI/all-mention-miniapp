"""Утилита для компиляции SCSS в CSS"""
import os
import logging
from pathlib import Path

try:
    import sass
except ImportError:
    try:
        import libsass as sass
    except ImportError:
        raise ImportError("Необходимо установить libsass: pip install libsass")

logger = logging.getLogger(__name__)

# Пути к файлам
BASE_DIR = Path(__file__).parent.parent
SCSS_DIR = BASE_DIR / 'static' / 'scss'
CSS_DIR = BASE_DIR / 'static' / 'css'
SCSS_FILE = SCSS_DIR / 'style.scss'
CSS_FILE = CSS_DIR / 'style.css'


def compile_scss(output_style='expanded', source_map=False):
    """
    Компилирует SCSS файлы в CSS
    
    Args:
        output_style: Стиль вывода ('expanded', 'compressed', 'compact', 'nested')
        source_map: Генерировать ли source map
    """
    try:
        if not SCSS_FILE.exists():
            logger.warning(f"SCSS файл не найден: {SCSS_FILE}")
            return False
        
        # Убеждаемся, что директория для CSS существует
        CSS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Компилируем SCSS
        # Используем строковый путь для совместимости
        css_content = sass.compile(
            filename=str(SCSS_FILE),
            output_style=output_style,
            include_paths=[str(SCSS_DIR)]
        )
        
        # Сохраняем CSS
        CSS_FILE.write_text(css_content, encoding='utf-8')
        
        logger.info(f"SCSS успешно скомпилирован: {SCSS_FILE} -> {CSS_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при компиляции SCSS: {e}", exc_info=True)
        return False


def watch_scss():
    """Отслеживает изменения в SCSS файлах и автоматически компилирует"""
    import time
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class SCSSHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith('.scss'):
                logger.info(f"Обнаружено изменение в {event.src_path}")
                compile_scss()
    
    event_handler = SCSSHandler()
    observer = Observer()
    observer.schedule(event_handler, str(SCSS_DIR), recursive=True)
    observer.start()
    
    logger.info(f"Отслеживание изменений SCSS запущено для {SCSS_DIR}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()


if __name__ == '__main__':
    # При запуске напрямую компилируем SCSS
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'watch':
        watch_scss()
    else:
        output_style = sys.argv[1] if len(sys.argv) > 1 else 'expanded'
        compile_scss(output_style=output_style)
