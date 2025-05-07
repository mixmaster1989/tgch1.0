"""
Модуль для диспетчеризации сигналов
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import time
from datetime import datetime, timedelta

from .models import CryptoSignal
from .notification.message_formatter import MessageFormatter
from .config import get_config

# Получаем логгер для модуля
logger = logging.getLogger('crypto.signal_dispatcher')

class SignalDispatcher:
    """
    Класс для диспетчеризации сигналов и отправки уведомлений
    """
    
    def __init__(self):
        """
        Инициализирует диспетчер сигналов
        """
        self.config = get_config()
        self.formatter = MessageFormatter()
        
        # Для отслеживания отправленных сигналов и соблюдения ограничений
        self.sent_signals = {}  # pair -> timestamp
        self.signals_per_hour = 0
        self.last_hour_reset = time.time()
        
        # Глобальная переменная для хранения экземпляра бота
        self._bot = None
        
        logger.info("Инициализирован диспетчер сигналов")
    
    def set_bot(self, bot):
        """
        Устанавливает экземпляр бота для отправки сообщений
        
        Args:
            bot: Экземпляр бота aiogram
        """
        self._bot = bot
        logger.info("Установлен бот для диспетчера сигналов")
    
    async def dispatch_signals(self, signals: List[CryptoSignal], chat_id: int) -> int:
        """
        Диспетчеризирует сигналы и отправляет уведомления
        
        Args:
            signals: Список сигналов для отправки
            chat_id: ID чата для отправки уведомлений
            
        Returns:
            int: Количество отправленных сигналов
        """
        if not self._bot:
            logger.error("Бот не установлен для диспетчера сигналов")
            return 0
        
        # Проверяем и сбрасываем счетчик сигналов в час
        current_time = time.time()
        if current_time - self.last_hour_reset > 3600:
            self.signals_per_hour = 0
            self.last_hour_reset = current_time
        
        # Получаем настройки для ограничений
        max_signals_per_hour = self.config['notification']['max_signals_per_hour']
        cooldown_per_pair = self.config['notification']['cooldown_per_pair']
        whitelist_pairs = self.config['notification']['whitelist_pairs']
        
        # Фильтруем и сортируем сигналы
        filtered_signals = []
        for signal in signals:
            # Проверяем, находится ли пара в белом списке
            if signal.pair not in whitelist_pairs:
                logger.debug(f"Сигнал для пары {signal.pair} отфильтрован (не в белом списке)")
                continue
            
            # Проверяем, не отправляли ли мы недавно сигнал для этой пары
            last_sent = self.sent_signals.get(signal.pair)
            if last_sent and (datetime.now() - last_sent).total_seconds() < cooldown_per_pair:
                logger.debug(f"Сигнал для пары {signal.pair} отфильтрован (слишком частые уведомления)")
                continue
            
            filtered_signals.append(signal)
        
        # Сортируем по уверенности (от высокой к низкой)
        filtered_signals.sort(key=lambda s: s.confidence, reverse=True)
        
        # Ограничиваем количество сигналов в час
        remaining_signals = max_signals_per_hour - self.signals_per_hour
        if remaining_signals <= 0:
            logger.warning("Достигнут лимит сигналов в час")
            return 0
        
        signals_to_send = filtered_signals[:remaining_signals]
        
        # Отправляем сигналы
        sent_count = 0
        for signal in signals_to_send:
            try:
                # Форматируем сообщение
                message_data = self.formatter.format_signal_message(signal)
                
                # Отправляем сообщение
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=message_data["text"],
                    reply_markup=message_data["keyboard"],
                    parse_mode=message_data["parse_mode"]
                )
                
                # Обновляем отслеживание
                self.sent_signals[signal.pair] = datetime.now()
                self.signals_per_hour += 1
                sent_count += 1
                
                logger.info(f"Отправлен сигнал для пары {signal.pair}")
                
                # Небольшая задержка между отправками
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Ошибка при отправке сигнала для пары {signal.pair}: {e}", exc_info=True)
        
        logger.info(f"Отправлено {sent_count} сигналов")
        return sent_count