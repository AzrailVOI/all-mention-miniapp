"""
Утилита для компиляции TypeScript в JavaScript
"""
import subprocess
import logging
import os
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


def compile_typescript(
    ts_dir: Optional[Path] = None,
    js_dir: Optional[Path] = None,
    tsconfig_path: Optional[Path] = None
) -> bool:
    """
    Компилирует TypeScript файлы в JavaScript.
    
    Args:
        ts_dir: Директория с TypeScript файлами (по умолчанию webapp/static/ts)
        js_dir: Директория для скомпилированных JS файлов (по умолчанию webapp/static/js)
        tsconfig_path: Путь к tsconfig.json (по умолчанию корень проекта)
    
    Returns:
        True если компиляция успешна, False в противном случае
    """
    # Определяем пути по умолчанию
    project_root = Path(__file__).parent.parent.parent
    if ts_dir is None:
        ts_dir = project_root / 'webapp' / 'static' / 'ts'
    if js_dir is None:
        js_dir = project_root / 'webapp' / 'static' / 'js'
    if tsconfig_path is None:
        tsconfig_path = project_root / 'tsconfig.json'
    
    # Проверяем наличие TypeScript файлов
    if not ts_dir.exists() or not any(ts_dir.glob('*.ts')):
        logger.warning(f"[TS Compiler] TypeScript файлы не найдены в {ts_dir}")
        return False
    
    # Проверяем наличие tsconfig.json
    if not tsconfig_path.exists():
        logger.error(f"[TS Compiler] tsconfig.json не найден: {tsconfig_path}")
        return False
    
    # Проверяем наличие tsc (сначала локально через npx, потом глобально)
    tsc_command: Optional[List[str]] = None
    
    # Проверяем локальный tsc через npx
    try:
        result = subprocess.run(
            ['npx', '--yes', 'tsc', '--version'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            tsc_command = ['npx', '--yes', 'tsc']
            logger.info("[TS Compiler] Используется локальный TypeScript через npx")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Если локальный не найден, проверяем глобальный
    if tsc_command is None:
        try:
            result = subprocess.run(
                ['tsc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                tsc_command = ['tsc']
                logger.info("[TS Compiler] Используется глобальный TypeScript")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    if tsc_command is None:
        logger.error("[TS Compiler] TypeScript компилятор (tsc) не найден. Установите: npm install -g typescript или добавьте в package.json")
        return False
    
    # Компилируем TypeScript
    try:
        logger.info(f"[TS Compiler] Компиляция TypeScript из {ts_dir} в {js_dir}...")
        compile_cmd = tsc_command + ['--project', str(tsconfig_path)]
        result = subprocess.run(
            compile_cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info(f"[TS Compiler] TypeScript успешно скомпилирован в {js_dir}")
            return True
        else:
            logger.error(f"[TS Compiler] Ошибка компиляции TypeScript:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("[TS Compiler] Таймаут при компиляции TypeScript")
        return False
    except Exception as e:
        logger.error(f"[TS Compiler] Неожиданная ошибка при компиляции: {e}")
        return False


def check_typescript_installed() -> bool:
    """
    Проверяет, установлен ли TypeScript компилятор.
    
    Returns:
        True если tsc доступен, False в противном случае
    """
    try:
        result = subprocess.run(
            ['tsc', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_typescript_locally(project_root: Optional[Path] = None) -> bool:
    """
    Устанавливает TypeScript локально в проект через npm.
    
    Args:
        project_root: Корень проекта (по умолчанию определяется автоматически)
    
    Returns:
        True если установка успешна, False в противном случае
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent
    
    # Проверяем наличие npm
    try:
        result = subprocess.run(
            ['npm', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            logger.error("[TS Compiler] npm не найден. Установите Node.js и npm")
            return False
    except FileNotFoundError:
        logger.error("[TS Compiler] npm не найден. Установите Node.js и npm")
        return False
    
    # Устанавливаем TypeScript локально
    try:
        logger.info("[TS Compiler] Установка TypeScript через npm...")
        result = subprocess.run(
            ['npm', 'install', '--save-dev', 'typescript'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            logger.info("[TS Compiler] TypeScript успешно установлен")
            return True
        else:
            logger.error(f"[TS Compiler] Ошибка установки TypeScript:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("[TS Compiler] Таймаут при установке TypeScript")
        return False
    except Exception as e:
        logger.error(f"[TS Compiler] Неожиданная ошибка при установке: {e}")
        return False
