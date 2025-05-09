"""
Сервис для управления уведомлениями о важных событиях
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import CryptoSignal
from .price_alerts import PriceAlertManager
from ..user_settings.user_preferences import UserPreferences

# Получаем логгер для модуля
logger = logging.getLogger('crypto.notification.alert_service')

class AlertService:
    """
    Сервис для управления уведомлениями о важных событиях
    """
    
    def __init__(self):
        """
        Инициализирует сервис уведомлений
        """
        self.price_alert_manager = PriceAlertManager()
        self.user_preferences = UserPreferences()
        
        # Для отслеживания пользователей, подписанных на уведомления
        self._subscribers = {}  # user_id -> {chat_id, settings}
        
        # Глобальная переменная для хранения экземпляра бота
        self._bot = None
        
        # Флаг для управления фоновым процессом
        self._running = False
        self._task = None
        
        logger.info("Инициализирован сервис уведомлений")
    
    def set_bot(self, bot):
        """
        Устанавливает экземпляр бота для отправки сообщений
        
        Args:
            bot: Экземпляр бота aiogram
        """
        self._bot = bot
        logger.info("Установлен бот для сервиса уведомлений")
    
    async def subscribe_user(self, user_id: int, chat_id: int) -> bool:
        """
        Подписывает пользователя на уведомления
        
        Args:
            user_id: ID пользователя
            chat_id: ID чата для отправки уведомлений
        """
        try:
            # Получаем настройки пользователя
            settings = await self.user_preferences.get_user_settings(user_id)
            
            # Сохраняем подписку
            self._subscribers[user_id] = {
                'chat_id': chat_id,
                'settings': settings
            }
            
            logger.info(f"Пользователь {user_id} подписан на уведомления")
            return True
        except Exception as e:
            logger.error(f"Ошибка при подписке пользователя {user_id}: {e}", exc_info=True)
            return False
    
    async def unsubscribe_user(self, user_id: int) -> bool:
        """
        Отписывает пользователя от уведомлений
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True, если пользователь успешно отписан
        """
        try:
            if user_id in self._subscribers:
                del self._subscribers[user_id]
                logger.info(f"Пользователь {user_id} отписан от уведомлений")
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
            # Сохраняем настройки в базе данных
            success = await self.user_preferences.save_user_settings(user_id, settings)
            
            # Обновляем настройки в списке подписчиков
            if success and user_id in self._subscribers:
                self._subscribers[user_id]['settings'] = settings
                logger.info(f"Обновлены настройки для пользователя {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"Ошибка при обновлении настроек пользователя {user_id}: {e}", exc_info=True)
            return False
    
    async def start_monitoring(self):
        """
        Запускает фоновый процесс мониторинга событий для отправки уведомлений
        """
        if self._running:
            logger.warning("Мониторинг уведомлений уже запущен")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Мониторинг уведомлений запущен")
    
    async def stop_monitoring(self):
        """
        Останавливает фоновый процесс мониторинга
        """
        if not self._running:
            logger.warning("Мониторинг не запущен")
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("Остановлен мониторинг важных событий")
    
    async def _monitoring_loop(self):
        """
        Основной цикл мониторинга событий для отправки уведомлений
        """
        while self._running:
            try:
                # Проверяем условия для отправки уведомлений
                await self._check_and_send_alerts()
                
                # Ждем перед следующей проверкой
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга уведомлений: {e}", exc_info=True)
                await asyncio.sleep(60)  # Ждем перед повторной попыткой

    async def _check_and_send_alerts(self):
        """
        Проверяет условия для отправки уведомлений и отправляет их
        """
        try:
            # Получаем все сигналы от менеджера ценовых алертов
            price_signals = await self.price_alert_manager.check_price_alerts()
            
            # Отправляем уведомления всем подписчикам
            for user_id, subscriber in self._subscribers.items():
                chat_id = subscriber['chat_id']
                settings = subscriber['settings']
                
                # Фильтруем сигналы по настройкам пользователя
                filtered_signals = self._filter_signals_by_settings(price_signals, settings)
                
                # Отправляем уведомления
                await self._send_alerts_to_subscriber(chat_id, filtered_signals)
        except Exception as e:
            logger.error(f"Ошибка при проверке и отправке уведомлений: {e}", exc_info=True)

    def _filter_signals_by_settings(self, signals, settings):
        """
        Фильтрует сигналы по настройкам пользователя
        
        Args:
            signals: Список сигналов
            settings: Настройки пользователя
        """
        # Реализация фильтрации сигналов
        return signals  # Пока возвращаем все сигналы без фильтрации

    async def _send_alerts_to_subscriber(self, chat_id: int, signals: List[CryptoSignal]):
        """
        Отправляет уведомления подписчику
        
        Args:
            chat_id: ID чата для отправки
            signals: Список сигналов для отправки
        """
        if not signals:
            return
        
        # Формируем сообщение
        message = self._format_alert_message(signals)
        
        try:
            # Отправляем сообщение
            await self._bot.send_message(chat_id, message)
            
            # Делаем небольшую паузу между сообщениями, чтобы не триггерить анти-спам систему
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений пользователю {chat_id}: {e}", exc_info=True)

    def _format_alert_message(self, signals: List[CryptoSignal]) -> str:
        """
        Форматирует список сигналов в текстовое сообщение
        
        Args:
            signals: Список сигналов
        """
        # Реализация форматирования сигналов в текстовое сообщение
        return "⚠️ Уведомление о важных событиях в криптовалютах:\n\n" + "\n".join(
            f"{signal.symbol}: {signal.signal_type} - {signal.value}" for signal in signals
        )

    async def test_alert(self, chat_id: int):
        """
        Отправляет тестовое уведомление
        
        Args:
            chat_id: ID чата для отправки
        """
        try:
            # Создаем тестовый сигнал
            test_signal = CryptoSignal(
                symbol="BTC",
                signal_type="price_alert",
                value=60000.0,
                timestamp=datetime.now(),
                confidence=0.95
            )
            
            # Отправляем тестовое уведомление
            await self._send_alerts_to_subscriber(chat_id, [test_signal])
        except Exception as e:
            logger.error(f"Ошибка при отправке тестового уведомления: {e}", exc_info=True)

# Создаем и экспортируем экземпляр сервиса уведомлений
alert_service = AlertService()