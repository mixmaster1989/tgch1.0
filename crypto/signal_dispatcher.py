"""
Модуль для диспетчеризации сигналов о криптовалютах
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import CryptoSignal, SignalType, SignalDirection
from .data_sources.crypto_data_manager import get_data_manager

# Получаем логгер для модуля
logger = logging.getLogger('crypto.signal_dispatcher')

class SignalDispatcher:
    """
    Класс для диспетчеризации сигналов о криптовалютах
    """
    
    def __init__(self):
        """
        Инициализирует диспетчер сигналов
        """
        # Глобальная переменная для хранения экземпляра бота
        self._bot = None
        
        # Список подписчиков на сигналы
        self._subscribers = {}  # user_id -> {chat_id, settings}
        
        # Флаг для управления фоновым процессом
        self._running = False
        self._task = None
        
        # Получаем менеджер данных
        self.data_manager = get_data_manager()
        
        logger.info("Инициализирован диспетчер сигналов")
    
    def set_bot(self, bot):
        """
        Устанавливает экземпляр бота для отправки сообщений
        
        Args:
            bot: Экземпляр бота aiogram
        """
        self._bot = bot
        logger.info("Установлен бот для диспетчера сигналов")
    
    async def start(self):
        """
        Запускает диспетчер сигналов
        """
        if self._running:
            logger.warning("Диспетчер сигналов уже запущен")
            return
        
        # Запускаем менеджер данных
        await self.data_manager.start()
        
        # Запускаем фоновый процесс
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Запущен диспетчер сигналов")
    
    async def stop(self):
        """
        Останавливает диспетчер сигналов
        """
        if not self._running:
            logger.warning("Диспетчер сигналов не запущен")
            return
        
        # Останавливаем фоновый процесс
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        # Останавливаем менеджер данных
        await self.data_manager.stop()
        
        logger.info("Остановлен диспетчер сигналов")
    
    async def _monitoring_loop(self):
        """
        Фоновый процесс для мониторинга и отправки сигналов
        """
        try:
            while self._running:
                try:
                    # Получаем данные о рынке
                    market_overview = await self.data_manager.get_market_overview()
                    
                    # Анализируем данные и генерируем сигналы
                    signals = await self._generate_signals(market_overview)
                    
                    if signals:
                        logger.info(f"Сгенерировано {len(signals)} сигналов")
                        
                        # Отправляем сигналы подписчикам
                        await self._send_signals_to_subscribers(signals)
                    
                    # Ждем перед следующей проверкой
                    await asyncio.sleep(300)  # Проверяем каждые 5 минут
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Ошибка в цикле мониторинга: {e}", exc_info=True)
                    await asyncio.sleep(60)  # Ждем перед повторной попыткой
        except asyncio.CancelledError:
            logger.info("Мониторинг отменен")
        except Exception as e:
            logger.error(f"Критическая ошибка в мониторинге: {e}", exc_info=True)
    
    async def _generate_signals(self, market_overview: Dict[str, Any]) -> List[CryptoSignal]:
        """
        Генерирует сигналы на основе данных о рынке
        
        Args:
            market_overview: Обзор рынка
            
        Returns:
            List[CryptoSignal]: Список сигналов
        """
        signals = []
        
        # Генерируем сигналы для топ растущих монет
        for coin in market_overview['top_gainers'][:3]:  # Берем только топ-3
            symbol = coin.get('symbol', '')
            price = coin.get('price', 0)
            change = coin.get('price_change_percent_24h', 0)
            
            if change > 10:  # Если рост более 10%
                signal = CryptoSignal(
                    id=f"{symbol}-{datetime.now().timestamp()}",
                    pair=f"{symbol}/USDT",
                    timestamp=datetime.now(),
                    signal_type=SignalType.VOLUME_SPIKE,
                    direction=SignalDirection.LONG,
                    price=price,
                    confidence=min(change / 20, 1.0),  # Максимум 1.0 при росте на 20%
                    description=f"Значительный рост {symbol}: +{change:.2f}% за 24 часа.",
                    metadata={
                        'price_change_percent': change,
                        'volume': coin.get('volume24h', 0)
                    }
                )
                signals.append(signal)
        
        # Генерируем сигналы для топ падающих монет
        for coin in market_overview['top_losers'][:3]:  # Берем только топ-3
            symbol = coin.get('symbol', '')
            price = coin.get('price', 0)
            change = coin.get('price_change_percent_24h', 0)
            
            if change < -10:  # Если падение более 10%
                signal = CryptoSignal(
                    id=f"{symbol}-{datetime.now().timestamp()}",
                    pair=f"{symbol}/USDT",
                    timestamp=datetime.now(),
                    signal_type=SignalType.VOLUME_SPIKE,
                    direction=SignalDirection.SHORT,
                    price=price,
                    confidence=min(abs(change) / 20, 1.0),  # Максимум 1.0 при падении на 20%
                    description=f"Значительное падение {symbol}: {change:.2f}% за 24 часа.",
                    metadata={
                        'price_change_percent': change,
                        'volume': coin.get('volume24h', 0)
                    }
                )
                signals.append(signal)
        
        return signals
    
    async def _send_signals_to_subscribers(self, signals: List[CryptoSignal]):
        """
        Отправляет сигналы подписчикам
        
        Args:
            signals: Список сигналов
        """
        if not self._bot:
            logger.error("Бот не установлен для диспетчера сигналов")
            return
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from .notification.message_formatter import MessageFormatter
        formatter = MessageFormatter()
        
        for user_id, subscriber in self._subscribers.items():
            chat_id = subscriber['chat_id']
            settings = subscriber['settings']
            
            # Фильтруем сигналы в соответствии с настройками пользователя
            user_signals = []
            for signal in signals:
                # Проверяем, отслеживает ли пользователь эту монету
                coin_symbol = signal.pair.split('/')[0]
                watched_coins = await self.user_preferences.get_user_watched_coins(user_id)
                
                if coin_symbol in watched_coins:
                    # Проверяем настройки уведомлений
                    if signal.signal_type == SignalType.VOLUME_SPIKE and settings['notifications']['volume_spikes']:
                        user_signals.append(signal)
            
            # Отправляем сигналы пользователю
            for signal in user_signals:
                try:
                    # Форматируем сообщение
                    message_data = formatter.format_signal_message(signal)
                    
                    # Отправляем сообщение
                    await self._bot.send_message(
                        chat_id=chat_id,
                        text=message_data["text"],
                        reply_markup=message_data["keyboard"],
                        parse_mode=message_data["parse_mode"]
                    )
                    
                    logger.info(f"Отправлен сигнал пользователю {user_id} для {signal.pair}")
                    
                    # Небольшая задержка между отправками
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Ошибка при отправке сигнала пользователю {user_id}: {e}", exc_info=True)
    
    async def subscribe_user(self, user_id: int, chat_id: int, settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Подписывает пользователя на сигналы
        
        Args:
            user_id: ID пользователя
            chat_id: ID чата для отправки сигналов
            settings: Настройки пользователя
            
        Returns:
            bool: True, если пользователь успешно подписан
        """
        try:
            if settings is None:
                # Настройки по умолчанию
                settings = {
                    'notifications': {
                        'price_change': True,
                        'psychological_levels': True,
                        'volume_spikes': True
                    }
                }
            
            # Добавляем пользователя в список подписчиков
            self._subscribers[user_id] = {
                'chat_id': chat_id,
                'settings': settings
            }
            
            logger.info(f"Пользователь {user_id} подписан на сигналы")
            return True
        except Exception as e:
            logger.error(f"Ошибка при подписке пользователя {user_id}: {e}", exc_info=True)
            return False
    
    async def unsubscribe_user(self, user_id: int) -> bool:
        """
        Отписывает пользователя от сигналов
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True, если пользователь успешно отписан
        """
        try:
            if user_id in self._subscribers:
                del self._subscribers[user_id]
                logger.info(f"Пользователь {user_id} отписан от сигналов")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при отписке пользователя {user_id}: {e}", exc_info=True)
            return False
    
    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """
        Обновляет настройки пользователя
        
        Args:
            user_id: ID пользователя
            settings: Новые настройки
            
        Returns:
            bool: True, если настройки успешно обновлены
        """
        try:
            if user_id in self._subscribers:
                self._subscribers[user_id]['settings'] = settings
                logger.info(f"Обновлены настройки для пользователя {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении настроек пользователя {user_id}: {e}", exc_info=True)
            return False