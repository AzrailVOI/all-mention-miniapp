// Управление модальным окном фильтров

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
    
    // Обработчик клика по overlay для закрытия модального окна
    const modalOverlay = document.getElementById(MODAL_ID);
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e: Event) => {
            // Закрываем только если клик был именно по overlay, а не по содержимому
            if (e.target === modalOverlay) {
                closeFiltersModal(e);
            }
        });
    }
    
    // Предотвращаем закрытие при клике внутри содержимого модального окна
    const modalContent = modalOverlay?.querySelector('.modal-content');
    if (modalContent) {
        modalContent.addEventListener('click', (e: Event) => {
            e.stopPropagation();
        });
    }
    
    // Обработчик кнопки закрытия
    const closeBtn = document.querySelector('.modal-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeFiltersModal();
        });
    }
    
    // Обработчик кнопки "Применить"
    const applyBtn = document.querySelector('.modal-btn-primary');
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            closeFiltersModal();
        });
    }
    
    // Обработчик кнопки "Сбросить"
    const resetBtn = document.querySelector('.modal-btn-secondary');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (window.resetFilters) {
                window.resetFilters();
            }
        });
    }
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
