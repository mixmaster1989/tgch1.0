"""
Утилиты для создания клавиатур в криптомодуле
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_crypto_main_keyboard() -> InlineKeyboardMarkup:
    """
    Создает основную клавиатуру для криптомодуля
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с основными опциями
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки
    builder.button(text="📊 Обзор рынка", callback_data="crypto_market_overview")
    builder.button(text="🔍 Smart Money сигналы", callback_data="crypto_smart_money")
    builder.button(text="⚙️ Настройки", callback_data="crypto_settings")
    
    # Настраиваем расположение - по одной кнопке в ряду
    builder.adjust(1)
    
    return builder.as_markup()

def get_coin_selection_keyboard(coins: list, page: int = 0, coins_per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора монет с пагинацией
    
    Args:
        coins: Список доступных монет
        page: Текущая страница
        coins_per_page: Количество монет на странице
        
    Returns:
        InlineKeyboardMarkup: Клавиатура с монетами и навигацией
    """
    builder = InlineKeyboardBuilder()
    
    # Вычисляем индексы для текущей страницы
    start_idx = page * coins_per_page
    end_idx = min(start_idx + coins_per_page, len(coins))
    
    # Добавляем кнопки для монет на текущей странице
    for i in range(start_idx, end_idx):
        coin = coins[i]
        builder.button(text=f"{coin['symbol']} - {coin['name']}", callback_data=f"crypto_select_coin_{coin['id']}")
    
    # Добавляем навигационные кнопки
    nav_row = []
    
    # Кнопка "Назад" если не первая страница
    if page > 0:
        nav_row.append(("⬅️ Назад", f"crypto_coins_page_{page-1}"))
    
    # Кнопка "Вперед" если не последняя страница
    if end_idx < len(coins):
        nav_row.append(("Вперед ➡️", f"crypto_coins_page_{page+1}"))
    
    # Добавляем навигационные кнопки
    for text, callback_data in nav_row:
        builder.button(text=text, callback_data=callback_data)
    
    # Добавляем кнопку возврата в главное меню
    builder.button(text="🔙 Вернуться в меню", callback_data="crypto_back_to_main")
    
    # Настраиваем расположение - по одной кнопке в ряду для монет
    # и навигационные кнопки в одном ряду
    builder.adjust(1, len(nav_row), 1)
    
    return builder.as_markup()