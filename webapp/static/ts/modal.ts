// Управление модальным окном фильтров
import { escapeHtml } from './utils';

const MODAL_ID = 'filtersModal';

/**
 * Открыть модальное окно фильтров
 */
export function openFiltersModal(): void {
    const modal = document.getElementById(MODAL_ID) as HTMLElement | null;
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        // Инициализируем иконки в модальном окне
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
}

/**
 * Закрыть модальное окно фильтров
 */
export function closeFiltersModal(event?: Event): void {
    // Если событие передано и клик был по overlay, закрываем
    if (event && event.target && (event.target as HTMLElement).id === MODAL_ID) {
        const modal = document.getElementById(MODAL_ID) as HTMLElement | null;
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    } else {
        // Закрываем при вызове без события (кнопка закрыть)
        const modal = document.getElementById(MODAL_ID) as HTMLElement | null;
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
}

/**
 * Инициализация обработчиков модального окна
 */
export function initModalHandlers(): void {
    // Закрытие модального окна по Escape
    document.addEventListener('keydown', (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById(MODAL_ID) as HTMLElement | null;
            if (modal && modal.style.display === 'flex') {
                closeFiltersModal();
            }
        }
    });
}

// Экспортируем функции в глобальную область для использования в HTML
declare global {
    interface Window {
        openFiltersModal: () => void;
        closeFiltersModal: (event?: Event) => void;
    }
}

window.openFiltersModal = openFiltersModal;
window.closeFiltersModal = closeFiltersModal;
