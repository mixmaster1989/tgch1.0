"""
Модуль для форматирования сообщений с сигналами
"""

import logging
from typing import Dict, Any
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from ..models import CryptoSignal, SignalDirection, MarketOverview

# Получаем логгер для модуля
logger = logging.getLogger('crypto.notification.formatter')

class MessageFormatter:
    """
    Класс для форматирования сообщений с сигналами
    """
    
    @staticmethod
    def format_signal_message(signal: CryptoSignal) -> Dict[str, Any]:
        """
        Форматирует сообщение с сигналом
        
        Args:
            signal: Сигнал для форматирования
            
        Returns:
            Dict[str, Any]: Словарь с текстом сообщения и клавиатурой
        """
        # Определяем эмодзи для направления
        direction_emoji = "🟢" if signal.direction == SignalDirection.LONG else "🔴"
        direction_text = "LONG" if signal.direction == SignalDirection.LONG else "SHORT"
        
        # Форматируем текст сообщения
        message_text = (
            f"📍 *{signal.pair}* | *{direction_text}* | Entry: *{signal.price:.4f}*\n\n"
            f"*Тип сигнала:* {signal.signal_type.value.replace('_', ' ').title()}\n"
            f"*Уверенность:* {'▓' * int(signal.confidence * 10)}{' ' * (10 - int(signal.confidence * 10))} ({signal.confidence:.2f})\n\n"
            f"*Описание:*\n{signal.description}\n\n"
            f"*Время:* {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 Подробнее", callback_data=f"crypto_details_{signal.id}")
        builder.button(text="🔕 Отключить уведомления", callback_data=f"crypto_mute_{signal.pair.replace('/', '_')}")
        builder.adjust(1)
        
        return {
            "text": message_text,
            "keyboard": builder.as_markup(),
            "parse_mode": "Markdown"
        }
    
    @staticmethod
    def format_market_overview(overview: MarketOverview) -> Dict[str, Any]:
        """
        Форматирует сообщение с обзором рынка
        
        Args:
            overview: Обзор рынка для форматирования
            
        Returns:
            Dict[str, Any]: Словарь с текстом сообщения и клавиатурой
        """
        # Форматируем данные о рынке
        market_cap_formatted = f"{overview.total_market_cap / 1_000_000_000:.2f}B"
        volume_formatted = f"{overview.total_volume_24h / 1_000_000_000:.2f}B"
        
        # Форматируем текст сообщения
        message_text = (
            f"📊 *Обзор криптовалютного рынка*\n\n"
            f"*Общая капитализация:* ${market_cap_formatted}\n"
            f"*Доминирование BTC:* {overview.btc_dominance:.2f}%\n"
            f"*Объем торгов (24ч):* ${volume_formatted}\n\n"
            f"*🟢 Топ растущих монет (24ч):*\n"
        )
        
        # Добавляем информацию о растущих монетах
        for i, coin in enumerate(overview.top_gainers):
            message_text += f"{i+1}. {coin['symbol']} - ${coin['price']:.4f} ({coin['change_24h']:.2f}%)\n"
        
        message_text += "\n*🔴 Топ падающих монет (24ч):*\n"
        
        # Добавляем информацию о падающих монетах
        for i, coin in enumerate(overview.top_losers):
            message_text += f"{i+1}. {coin['symbol']} - ${coin['price']:.4f} ({coin['change_24h']:.2f}%)\n"
        
        message_text += f"\n*Обновлено:* {overview.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Обновить", callback_data="crypto_refresh_market")
        builder.button(text="📈 Сигналы Smart Money", callback_data="crypto_smart_money")
        builder.button(text="🔙 Назад", callback_data="crypto_back_to_main")
        builder.adjust(1)
        
        return {
            "text": message_text,
            "keyboard": builder.as_markup(),
            "parse_mode": "Markdown"
        }