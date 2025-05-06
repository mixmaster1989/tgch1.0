import logging
import asyncio
import random
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import Channel, Message
import os
import yaml
import time
from datetime import datetime, timedelta
from core.generator import generate_post

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
        return {}

# Класс для управления комментированием
class CommentingManager:
    def __init__(self, api_id=None, api_hash=None, phone=None, session_name='commenting_session'):
        """
        Инициализация менеджера комментирования
        
        Args:
            api_id (int): API ID для Telegram API
            api_hash (str): API Hash для Telegram API
            phone (str): Номер телефона для авторизации
            session_name (str): Имя сессии
        """
        config = load_config()
        
        # Загрузка настроек из конфигурации или использование переданных параметров
        self.api_id = api_id or config.get('telegram_api', {}).get('api_id')
        self.api_hash = api_hash or config.get('telegram_api', {}).get('api_hash')
        self.phone = phone or config.get('telegram_api', {}).get('phone')
        self.session_name = session_name
        
        # Настройки безопасности (по умолчанию)
        self.safe_settings = {
            'comments_per_day': 30,  # Максимальное количество комментариев в день
            'delay_between_comments': 120,  # Задержка между комментариями в секундах
            'max_comments_per_channel': 5,  # Максимальное количество комментариев в одном канале
            'daily_reset_time': '00:00',  # Время сброса счетчика комментариев
        }
        
        # Загрузка настроек безопасности из конфигурации
        if 'commenting' in config and 'safe_settings' in config['commenting']:
            self.safe_settings.update(config['commenting']['safe_settings'])
        
        # Счетчики для отслеживания лимитов
        self.today_comments = 0
        self.last_comment_time = None
        self.last_reset_date = datetime.now().date()
        self.channel_comments = {}  # Словарь для отслеживания комментариев по каналам
        
        # Клиент Telegram
        self.client = None
        
        # Флаг авторизации
        self.is_authorized = False
        
        # Шаблоны комментариев
        self.comment_templates = [
            "Интересная статья! {channel_mention}",
            "Спасибо за информацию! Кстати, у нас в {channel_mention} тоже много полезного контента по этой теме.",
            "Отличный пост! Мы в {channel_mention} недавно обсуждали похожую тему.",
            "Хорошая статья! Заходите к нам в {channel_mention} за дополнительной информацией.",
            "Полезно! В {channel_mention} есть еще много интересного по этой теме."
        ]
        
        # Загрузка шаблонов комментариев из конфигурации
        if 'commenting' in config and 'templates' in config['commenting']:
            self.comment_templates = config['commenting']['templates']
    
    async def connect(self):
        """
        Подключение к Telegram API
        
        Returns:
            bool: True, если подключение успешно, иначе False
        """
        if not self.api_id or not self.api_hash:
            logger.error("API ID или API Hash не указаны")
            return False
        
        try:
            # Создание клиента
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            
            # Подключение
            await self.client.connect()
            
            # Проверка авторизации
            if not await self.client.is_user_authorized():
                if not self.phone:
                    logger.error("Номер телефона не указан")
                    return False
                
                # Отправка кода подтверждения
                await self.client.send_code_request(self.phone)
                logger.info(f"Код подтверждения отправлен на номер {self.phone}")
                
                # Здесь нужно будет ввести код подтверждения
                # В реальном приложении это может быть реализовано через бота
                return False
            
            self.is_authorized = True
            logger.info("Успешное подключение к Telegram API")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при подключении к Telegram API: {e}")
            return False
    
    async def sign_in_with_code(self, code):
        """
        Авторизация с помощью кода подтверждения
        
        Args:
            code (str): Код подтверждения
            
        Returns:
            bool: True, если авторизация успешна, иначе False
        """
        if not self.client:
            logger.error("Клиент не инициализирован")
            return False
        
        try:
            # Авторизация с помощью кода
            await self.client.sign_in(self.phone, code)
            self.is_authorized = True
            logger.info("Успешная авторизация")
            return True
        except errors.SessionPasswordNeededError:
            logger.error("Требуется пароль двухфакторной аутентификации")
            return False
        except Exception as e:
            logger.error(f"Ошибка при авторизации: {e}")
            return False
    
    async def sign_in_with_password(self, password):
        """
        Авторизация с помощью пароля двухфакторной аутентификации
        
        Args:
            password (str): Пароль двухфакторной аутентификации
            
        Returns:
            bool: True, если авторизация успешна, иначе False
        """
        if not self.client:
            logger.error("Клиент не инициализирован")
            return False
        
        try:
            # Авторизация с помощью пароля
            await self.client.sign_in(password=password)
            self.is_authorized = True
            logger.info("Успешная авторизация с двухфакторной аутентификацией")
            return True
        except Exception as e:
            logger.error(f"Ошибка при авторизации с паролем: {e}")
            return False
    
    async def disconnect(self):
        """
        Отключение от Telegram API
        """
        if self.client:
            await self.client.disconnect()
            logger.info("Отключение от Telegram API")
    
    async def join_channel(self, channel_username):
        """
        Присоединение к каналу
        
        Args:
            channel_username (str): Имя пользователя канала
            
        Returns:
            bool: True, если присоединение успешно, иначе False
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return False
        
        try:
            # Присоединение к каналу
            await self.client(JoinChannelRequest(channel_username))
            logger.info(f"Успешное присоединение к каналу {channel_username}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при присоединении к каналу {channel_username}: {e}")
            return False
    
    async def get_channel_by_username(self, username):
        """
        Получение сущности канала по имени пользователя
        
        Args:
            username (str): Имя пользователя канала
            
        Returns:
            Channel: Сущность канала
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return None
        
        try:
            # Получение сущности канала
            entity = await self.client.get_entity(username)
            if isinstance(entity, Channel):
                return entity
            else:
                logger.error(f"{username} не является каналом")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении канала {username}: {e}")
            return None
    
    async def get_channel_posts(self, channel_entity, limit=10):
        """
        Получение последних постов канала
        
        Args:
            channel_entity: Сущность канала
            limit (int): Максимальное количество постов
            
        Returns:
            list: Список постов
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Получение истории сообщений
            history = await self.client(GetHistoryRequest(
                peer=channel_entity,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            # Фильтрация сообщений (только посты)
            posts = [msg for msg in history.messages if isinstance(msg, Message) and not msg.reply_to_msg_id]
            return posts
        except Exception as e:
            logger.error(f"Ошибка при получении постов канала: {e}")
            return []
    
    async def comment_post(self, post, comment_text, safe_mode=True):
        """
        Комментирование поста
        
        Args:
            post: Пост для комментирования
            comment_text (str): Текст комментария
            safe_mode (bool): Использовать безопасный режим
            
        Returns:
            bool: True, если комментирование успешно, иначе False
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return False
        
        # Проверка лимитов в безопасном режиме
        if safe_mode:
            # Сброс счетчика в новый день
            today = datetime.now().date()
            if today > self.last_reset_date:
                self.today_comments = 0
                self.channel_comments = {}
                self.last_reset_date = today
            
            # Проверка дневного лимита
            if self.today_comments >= self.safe_settings['comments_per_day']:
                logger.warning("Достигнут дневной лимит комментариев")
                return False
            
            # Проверка лимита комментариев для канала
            channel_id = post.peer_id.channel_id
            if channel_id in self.channel_comments and self.channel_comments[channel_id] >= self.safe_settings['max_comments_per_channel']:
                logger.warning(f"Достигнут лимит комментариев для канала {channel_id}")
                return False
            
            # Проверка времени последнего комментария
            if self.last_comment_time:
                elapsed = (datetime.now() - self.last_comment_time).total_seconds()
                if elapsed < self.safe_settings['delay_between_comments']:
                    delay = self.safe_settings['delay_between_comments'] - elapsed
                    logger.info(f"Ожидание {delay:.2f} секунд перед следующим комментарием")
                    await asyncio.sleep(delay)
        
        try:
            # Комментирование поста
            await self.client.send_message(
                entity=post.peer_id,
                message=comment_text,
                reply_to=post.id
            )
            
            # Обновление счетчиков
            self.today_comments += 1
            self.last_comment_time = datetime.now()
            
            # Обновление счетчика комментариев для канала
            channel_id = post.peer_id.channel_id
            if channel_id not in self.channel_comments:
                self.channel_comments[channel_id] = 0
            self.channel_comments[channel_id] += 1
            
            logger.info(f"Успешно прокомментирован пост {post.id}")
            return True
        
        except errors.FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"FloodWaitError: Необходимо подождать {wait_time} секунд")
            
            if safe_mode:
                # Уменьшаем лимиты в случае FloodWaitError
                self.safe_settings['comments_per_day'] = max(5, self.safe_settings['comments_per_day'] // 2)
                self.safe_settings['delay_between_comments'] *= 2
                logger.info(f"Лимиты уменьшены: {self.safe_settings}")
            
            return False
        
        except Exception as e:
            logger.error(f"Ошибка при комментировании поста: {e}")
            return False
    
    def generate_comment(self, channel_mention):
        """
        Генерация комментария
        
        Args:
            channel_mention (str): Упоминание канала
            
        Returns:
            str: Сгенерированный комментарий
        """
        # Выбор случайного шаблона
        template = random.choice(self.comment_templates)
        
        # Форматирование шаблона
        comment = template.format(channel_mention=channel_mention)
        
        return comment
    
    async def generate_ai_comment(self, post_text, channel_mention):
        """
        Генерация комментария с использованием ИИ
        
        Args:
            post_text (str): Текст поста
            channel_mention (str): Упоминание канала
            
        Returns:
            str: Сгенерированный комментарий
        """
        try:
            # Создание промпта для генерации комментария
            prompt = f"Напиши короткий комментарий (1-2 предложения) к посту в Telegram. Пост: \"{post_text[:100]}...\". В конце комментария упомяни канал {channel_mention}."
            
            # Генерация комментария с использованием ИИ
            # Здесь можно использовать любую модель генерации текста
            # В данном примере используется функция generate_post из модуля generator
            comment = generate_post("informational", "tech")
            
            # Добавление упоминания канала, если его нет в комментарии
            if channel_mention not in comment:
                comment += f"\n\nПодробнее в {channel_mention}"
            
            return comment
        except Exception as e:
            logger.error(f"Ошибка при генерации комментария с использованием ИИ: {e}")
            return self.generate_comment(channel_mention)
    
    async def comment_channel_posts(self, target_channel_username, own_channel_username, limit=5, use_ai=False, safe_mode=True):
        """
        Комментирование постов в канале
        
        Args:
            target_channel_username (str): Имя пользователя целевого канала
            own_channel_username (str): Имя пользователя собственного канала
            limit (int): Максимальное количество постов для комментирования
            use_ai (bool): Использовать ИИ для генерации комментариев
            safe_mode (bool): Использовать безопасный режим
            
        Returns:
            dict: Результаты комментирования
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return {"success": 0, "failed": 0, "details": "Не авторизован"}
        
        # Результаты комментирования
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        try:
            # Получение целевого канала
            target_channel = await self.get_channel_by_username(target_channel_username)
            if not target_channel:
                return {"success": 0, "failed": 0, "details": f"Канал {target_channel_username} не найден"}
            
            # Присоединение к каналу (если необходимо)
            try:
                await self.join_channel(target_channel_username)
            except Exception as e:
                logger.warning(f"Не удалось присоединиться к каналу {target_channel_username}: {e}")
            
            # Получение постов канала
            posts = await self.get_channel_posts(target_channel, limit=limit)
            
            # Ограничение количества постов для комментирования
            if safe_mode:
                max_comments = min(
                    self.safe_settings['max_comments_per_channel'],
                    self.safe_settings['comments_per_day'] - self.today_comments
                )
                posts = posts[:max_comments]
            
            # Комментирование постов
            for post in posts:
                # Генерация комментария
                if use_ai and hasattr(post, 'message') and post.message:
                    comment_text = await self.generate_ai_comment(post.message, own_channel_username)
                else:
                    comment_text = self.generate_comment(own_channel_username)
                
                # Комментирование поста
                success = await self.comment_post(post, comment_text, safe_mode=safe_mode)
                
                if success:
                    results["success"] += 1
                    results["details"].append(f"Успешно прокомментирован пост {post.id}")
                else:
                    results["failed"] += 1
                    results["details"].append(f"Не удалось прокомментировать пост {post.id}")
                
                # Задержка между комментариями
                if safe_mode and post != posts[-1]:
                    delay = random.uniform(
                        self.safe_settings['delay_between_comments'],
                        self.safe_settings['delay_between_comments'] * 1.5
                    )
                    logger.info(f"Ожидание {delay:.2f} секунд перед следующим комментарием")
                    await asyncio.sleep(delay)
            
            return results
        
        except Exception as e:
            logger.error(f"Ошибка при комментировании постов: {e}")
            return {
                "success": results["success"],
                "failed": results["failed"] + 1,
                "details": results["details"] + [f"Ошибка: {e}"]
            }
    
    def save_settings(self):
        """
        Сохранение настроек в конфигурационный файл
        
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
        try:
            # Загрузка текущей конфигурации
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
            # Обновление настроек комментирования
            if 'commenting' not in config:
                config['commenting'] = {}
            
            config['commenting']['safe_settings'] = self.safe_settings
            config['commenting']['templates'] = self.comment_templates
            
            # Сохранение конфигурации
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False)
            
            logger.info("Настройки комментирования сохранены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек: {e}")
            return False

# Пример использования
async def example_usage():
    # Создание менеджера комментирования
    manager = CommentingManager(
        api_id=12345,  # Замените на свой API ID
        api_hash="your_api_hash",  # Замените на свой API Hash
        phone="+1234567890"  # Замените на свой номер телефона
    )
    
    # Подключение к Telegram API
    if await manager.connect():
        try:
            # Комментирование постов в канале
            results = await manager.comment_channel_posts(
                target_channel_username="example_channel",
                own_channel_username="@your_channel",
                limit=3,
                use_ai=True,
                safe_mode=True
            )
            print(f"Результаты комментирования: {results}")
        finally:
            # Отключение от Telegram API
            await manager.disconnect()

if __name__ == "__main__":
    # Запуск примера использования
    asyncio.run(example_usage())