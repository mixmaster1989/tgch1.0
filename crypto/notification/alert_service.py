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
            
        Returns:
            bool: True, если пользователь успешно подписан
        """
        try:
            # Получаем настройки пользователя
            settings = await self.user_preferences.get_user_settings(user_id)
            
            # Добавляем пользователя в список подписчиков
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
        Запускает фоновый процесс мониторинга и отправки уведомлений
        """
        if self._running:
            logger.warning("Мониторинг уже запущен")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Запущен мониторинг важных событий")
    
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
        Фоновый процесс для мониторинга и отправки уведомлений
        """
        try:
            while self._running:
                try:
                    # Получаем все уведомления
                    alerts = await self.price_alert_manager.get_all_alerts()
                    
                    if alerts:
                        logger.info(f"Получено {len(alerts)} уведомлений")
                        
                        # Отправляем уведомления подписчикам
                        await self._send_alerts_to_subscribers(alerts)
                    
                    # Ждем перед следующей проверкой
                    await asyncio.sleep(60)  # Проверяем каждую минуту
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Ошибка в цикле мониторинга: {e}", exc_info=True)
                    await asyncio.sleep(60)  # Ждем перед повторной попыткой
        except asyncio.CancelledError:
            logger.info("Мониторинг отменен")
        except Exception as e:
            logger.error(f"Критическая ошибка в мониторинге: {e}", exc_info=True)
    
    async def _send_alerts_to_subscribers(self, alerts: List[CryptoSignal]):
        """
        Отправляет уведомления подписчикам
        
        Args:
            alerts: Список уведомлений
        """
        if not self._bot:
            logger.error("Бот не установлен для сервиса уведомлений")
            return
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from .message_formatter import MessageFormatter
        formatter = MessageFormatter()
        
        for user_id, subscriber in self._subscribers.items():
            chat_id = subscriber['chat_id']
            settings = subscriber['settings']
            
            # Фильтруем уведомления в соответствии с настройками пользователя
            user_alerts = []
            for alert in alerts:
                # Проверяем, отслеживает ли пользователь эту монету
                coin_symbol = alert.pair.split('/')[0]
                watched_coins = await self.user_preferences.get_user_watched_coins(user_id)
                
                if coin_symbol in watched_coins:
                    # Проверяем настройки уведомлений
                    if "price_change" in alert.description.lower() and settings['notifications']['price_change']:
                        user_alerts.append(alert)
                    elif "психологический" in alert.description.lower() and settings['notifications']['psychological_levels']:
                        user_alerts.append(alert)
                    elif "всплеск объема" in alert.description.lower() and settings['notifications']['volume_spikes']:
                        user_alerts.append(alert)
            
            # Отправляем уведомления пользователю
            for alert in user_alerts:
                try:
                    # Форматируем сообщение
                    message_data = formatter.format_signal_message(alert)
                    
                    # Отправляем сообщение
                    await self._bot.send_message(
                        chat_id=chat_id,
                        text=message_data["text"],
                        reply_markup=message_data["keyboard"],
                        parse_mode=message_data["parse_mode"]
                    )
                    
                    logger.info(f"Отправлено уведомление пользователю {user_id} для {alert.pair}")
                    
                    # Небольшая задержка между отправками
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}", exc_info=True)
    
    async def send_test_alert(self, user_id: int, coin_symbol: str) -> bool:
        """
        Отправляет тестовое уведомление пользователю
        
        Args:
            user_id: ID пользователя
            coin_symbol: Символ монеты
            
        Returns:
            bool: True, если уведомление успешно отправлено
        """
        if not self._bot:
            logger.error("Бот не установлен для сервиса уведомлений")
            return False
        
        if user_id not in self._subscribers:
            logger.error(f"Пользователь {user_id} не подписан на уведомления")
            return False
        
        try:
            # Создаем тестовое уведомление
            import uuid
            from ..models import CryptoSignal, SignalType, SignalDirection
            
            test_signal = CryptoSignal(
                id=str(uuid.uuid4()),
                pair=f"{coin_symbol}/USDT",
                timestamp=datetime.now(),
                signal_type=SignalType.VOLUME_SPIKE,
                direction=SignalDirection.LONG,
                price=1000.0,
                confidence=0.9,
                description=f"Тестовое уведомление для {coin_symbol}. Это сообщение отправлено для проверки работы системы уведомлений.",
                metadata={}
            )
            
            # Импортируем здесь, чтобы избежать циклических импортов
            from .message_formatter import MessageFormatter
            formatter = MessageFormatter()
            
            # Форматируем сообщение
            message_data = formatter.format_signal_message(test_signal)
            
            # Отправляем сообщение
            chat_id = self._subscribers[user_id]['chat_id']
            await self._bot.send_message(
                chat_id=chat_id,
                text=message_data["text"],
                reply_markup=message_data["keyboard"],
                parse_mode=message_data["parse_mode"]
            )
            
            logger.info(f"Отправлено тестовое уведомление пользователю {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке тестового уведомления: {e}", exc_info=True)
            return False