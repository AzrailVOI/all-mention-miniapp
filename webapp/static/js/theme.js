// Управление темой

/**
 * Инициализация темы при загрузке
 */
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.className = savedTheme === 'light' ? 'theme-light' : '';
    updateThemeIcon(savedTheme);
}

/**
 * Переключение темы
 */
function toggleTheme() {
    const isLight = document.body.classList.contains('theme-light');
    const newTheme = isLight ? 'dark' : 'light';
    document.body.className = newTheme === 'light' ? 'theme-light' : '';
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

/**
 * Обновление иконки темы
 */
function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon && window.lucide) {
        icon.setAttribute('data-lucide', theme === 'light' ? 'moon' : 'sun');
        window.lucide.createIcons();
    }
}

// Экспорт в window
window.initTheme = initTheme;
window.toggleTheme = toggleTheme;
