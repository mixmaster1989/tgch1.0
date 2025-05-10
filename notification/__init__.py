"""
Инициализационный файл для пакета notification.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class NotificationHandler:
    @staticmethod
    def get_signal_keyboard(signal: dict) -> InlineKeyboardMarkup:
        """
        Создание клавиатуры с кнопкой Cryptorank для сигнала
        """
        keyboard = [[
            InlineKeyboardButton(
                text="🔍 Cryptorank",
                callback_data=f"cr_{signal['pair']}"
            )
        ]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_callback_query_handler(query):
        """
        Обработчик callback-запросов
        """
        if query.data.startswith('cr_'):
            pair = query.data[3:]
            # Здесь может быть реализована логика обработки нажатия на кнопку
            query.answer(f"Открытие Cryptorank для {pair}")