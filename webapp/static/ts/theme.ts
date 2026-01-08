// Управление темой

/**
 * Инициализация темы при загрузке
 */
export function initTheme(): void {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.className = savedTheme === 'light' ? 'theme-light' : '';
    updateThemeIcon(savedTheme);
}

/**
 * Переключение темы
 */
export function toggleTheme(): void {
    const isLight = document.body.classList.contains('theme-light');
    const newTheme = isLight ? 'dark' : 'light';
    document.body.className = newTheme === 'light' ? 'theme-light' : '';
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

/**
 * Обновление иконки темы
 */
function updateThemeIcon(theme: string): void {
    const icon = document.getElementById('theme-icon');
    if (icon && window.lucide) {
        icon.setAttribute('data-lucide', theme === 'light' ? 'moon' : 'sun');
        window.lucide.createIcons();
    }
}

// Экспортируем функции в глобальную область для использования в HTML
declare global {
    interface Window {
        toggleTheme: () => void;
    }
}

window.toggleTheme = toggleTheme;
