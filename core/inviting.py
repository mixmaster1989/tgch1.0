import logging
import asyncio
import random
from telethon import TelegramClient, errors, functions
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.tl.types import Channel, User
import os
import yaml
import time
from datetime import datetime, timedelta

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

# Класс для управления инвайтингом
class InvitingManager:
    def __init__(self, api_id=None, api_hash=None, phone=None, session_name='inviting_session'):
        """
        Инициализация менеджера инвайтинга
        
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
            'invites_per_day': 50,  # Максимальное количество приглашений в день
            'delay_between_invites': 60,  # Задержка между приглашениями в секундах
            'max_invites_per_batch': 5,  # Максимальное количество приглашений за один раз
            'daily_reset_time': '00:00',  # Время сброса счетчика приглашений
        }
        
        # Загрузка настроек безопасности из конфигурации
        if 'inviting' in config and 'safe_settings' in config['inviting']:
            self.safe_settings.update(config['inviting']['safe_settings'])
        
        # Счетчики для отслеживания лимитов
        self.today_invites = 0
        self.last_invite_time = None
        self.last_reset_date = datetime.now().date()
        
        # Клиент Telegram
        self.client = None
        
        # Флаг авторизации
        self.is_authorized = False
    
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
    
    async def get_dialogs(self, limit=100):
        """
        Получение списка диалогов
        
        Args:
            limit (int): Максимальное количество диалогов
            
        Returns:
            list: Список диалогов
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Получение диалогов
            result = await self.client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=limit,
                hash=0
            ))
            
            return result.dialogs
        except Exception as e:
            logger.error(f"Ошибка при получении диалогов: {e}")
            return []
    
    async def get_group_members(self, group_entity, limit=200):
        """
        Получение списка участников группы
        
        Args:
            group_entity: Сущность группы
            limit (int): Максимальное количество участников
            
        Returns:
            list: Список участников
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Получение участников группы
            participants = await self.client.get_participants(group_entity, limit=limit)
            return participants
        except Exception as e:
            logger.error(f"Ошибка при получении участников группы: {e}")
            return []
    
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
    
    async def invite_users_to_channel(self, channel_entity, users, safe_mode=True):
        """
        Приглашение пользователей в канал
        
        Args:
            channel_entity: Сущность канала
            users (list): Список пользователей для приглашения
            safe_mode (bool): Использовать безопасный режим
            
        Returns:
            dict: Результаты приглашения
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return {"success": 0, "failed": len(users), "details": "Не авторизован"}
        
        # Проверка лимитов в безопасном режиме
        if safe_mode:
            # Сброс счетчика в новый день
            today = datetime.now().date()
            if today > self.last_reset_date:
                self.today_invites = 0
                self.last_reset_date = today
            
            # Проверка дневного лимита
            if self.today_invites >= self.safe_settings['invites_per_day']:
                logger.warning("Достигнут дневной лимит приглашений")
                return {
                    "success": 0, 
                    "failed": len(users), 
                    "details": "Достигнут дневной лимит приглашений"
                }
        
        # Результаты приглашения
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        try:
            # Преобразование пользователей в InputPeerUser
            user_peers = []
            for user in users:
                if isinstance(user, User):
                    try:
                        user_peer = InputPeerUser(user.id, user.access_hash)
                        user_peers.append(user_peer)
                    except Exception as e:
                        logger.error(f"Ошибка при создании InputPeerUser: {e}")
                        results["failed"] += 1
                        results["details"].append(f"Ошибка для пользователя {user.id}: {e}")
            
            # Приглашение пользователей
            batch_size = self.safe_settings['max_invites_per_batch'] if safe_mode else len(user_peers)
            
            for i in range(0, len(user_peers), batch_size):
                batch = user_peers[i:i+batch_size]
                
                # Проверка времени последнего приглашения
                if safe_mode and self.last_invite_time:
                    elapsed = (datetime.now() - self.last_invite_time).total_seconds()
                    if elapsed < self.safe_settings['delay_between_invites']:
                        delay = self.safe_settings['delay_between_invites'] - elapsed
                        logger.info(f"Ожидание {delay:.2f} секунд перед следующим приглашением")
                        await asyncio.sleep(delay)
                
                try:
                    # Приглашение пользователей
                    await self.client(InviteToChannelRequest(
                        channel=channel_entity,
                        users=batch
                    ))
                    
                    # Обновление счетчиков
                    results["success"] += len(batch)
                    self.today_invites += len(batch)
                    self.last_invite_time = datetime.now()
                    
                    logger.info(f"Успешно приглашено {len(batch)} пользователей")
                    
                    # Задержка между батчами
                    if safe_mode and i + batch_size < len(user_peers):
                        delay = random.uniform(
                            self.safe_settings['delay_between_invites'],
                            self.safe_settings['delay_between_invites'] * 1.5
                        )
                        logger.info(f"Ожидание {delay:.2f} секунд перед следующим батчем")
                        await asyncio.sleep(delay)
                
                except errors.FloodWaitError as e:
                    wait_time = e.seconds
                    logger.warning(f"FloodWaitError: Необходимо подождать {wait_time} секунд")
                    results["failed"] += len(batch)
                    results["details"].append(f"FloodWaitError: Необходимо подождать {wait_time} секунд")
                    
                    if safe_mode:
                        # Уменьшаем лимиты в случае FloodWaitError
                        self.safe_settings['invites_per_day'] = max(10, self.safe_settings['invites_per_day'] // 2)
                        self.safe_settings['delay_between_invites'] *= 2
                        logger.info(f"Лимиты уменьшены: {self.safe_settings}")
                    
                    break
                
                except Exception as e:
                    logger.error(f"Ошибка при приглашении пользователей: {e}")
                    results["failed"] += len(batch)
                    results["details"].append(f"Ошибка при приглашении: {e}")
            
            return results
        
        except Exception as e:
            logger.error(f"Ошибка при приглашении пользователей: {e}")
            return {
                "success": results["success"],
                "failed": len(users) - results["success"],
                "details": f"Ошибка: {e}"
            }
    
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
            
    async def parse_group_members(self, group_username, limit=1000):
        """
        Парсинг участников группы или канала
        
        Args:
            group_username (str): Имя пользователя группы или канала
            limit (int): Максимальное количество участников для парсинга
            
        Returns:
            list: Список участников
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Получение сущности группы или канала
            group_entity = await self.client.get_entity(group_username)
            
            # Получение участников
            participants = await self.client.get_participants(group_entity, limit=limit)
            
            logger.info(f"Успешно получено {len(participants)} участников из {group_username}")
            return participants
        except Exception as e:
            logger.error(f"Ошибка при парсинге участников из {group_username}: {e}")
            return []
    
    async def search_users_by_keyword(self, keyword, limit=100):
        """
        Поиск пользователей по ключевому слову или хештегу
        
        Args:
            keyword (str): Ключевое слово или хештег
            limit (int): Максимальное количество результатов
            
        Returns:
            list: Список найденных пользователей
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Поиск по ключевому слову
            results = await self.client.search_global(keyword, limit=limit)
            
            # Фильтрация только пользователей
            users = [result.entity for result in results if isinstance(result.entity, User)]
            
            logger.info(f"Найдено {len(users)} пользователей по запросу '{keyword}'")
            return users
        except Exception as e:
            logger.error(f"Ошибка при поиске пользователей по запросу '{keyword}': {e}")
            return []
    
    async def parse_comments_from_post(self, channel_username, post_id, limit=100):
        """
        Парсинг пользователей из комментариев к посту
        
        Args:
            channel_username (str): Имя пользователя канала
            post_id (int): ID поста
            limit (int): Максимальное количество комментариев
            
        Returns:
            list: Список пользователей, оставивших комментарии
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Получение сущности канала
            channel_entity = await self.client.get_entity(channel_username)
            
            # Получение поста
            post = await self.client.get_messages(channel_entity, ids=post_id)
            
            # Получение комментариев
            comments = await self.client.get_messages(
                channel_entity,
                reply_to=post_id,
                limit=limit
            )
            
            # Извлечение пользователей из комментариев
            users = [comment.sender for comment in comments if comment.sender]
            
            logger.info(f"Получено {len(users)} пользователей из комментариев к посту {post_id}")
            return users
        except Exception as e:
            logger.error(f"Ошибка при парсинге комментариев: {e}")
            return []
    
    async def parse_active_chat_users(self, chat_username, hours=24, limit=200):
        """
        Парсинг активных пользователей из чата
        
        Args:
            chat_username (str): Имя пользователя чата
            hours (int): Количество часов для определения активности
            limit (int): Максимальное количество сообщений для анализа
            
        Returns:
            list: Список активных пользователей
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Получение сущности чата
            chat_entity = await self.client.get_entity(chat_username)
            
            # Определение времени начала
            start_time = datetime.now() - timedelta(hours=hours)
            
            # Получение сообщений
            messages = await self.client.get_messages(
                chat_entity,
                limit=limit,
                offset_date=start_time
            )
            
            # Извлечение уникальных пользователей
            user_ids = set()
            users = []
            
            for message in messages:
                if message.sender_id and message.sender_id not in user_ids:
                    user_ids.add(message.sender_id)
                    try:
                        user = await self.client.get_entity(message.sender_id)
                        if isinstance(user, User):
                            users.append(user)
                    except:
                        pass
            
            logger.info(f"Получено {len(users)} активных пользователей из чата {chat_username}")
            return users
        except Exception as e:
            logger.error(f"Ошибка при парсинге активных пользователей: {e}")
            return []
    
    async def find_similar_channels(self, channel_username, limit=10):
        """
        Поиск похожих каналов
        
        Args:
            channel_username (str): Имя пользователя канала
            limit (int): Максимальное количество похожих каналов
            
        Returns:
            list: Список похожих каналов
        """
        if not self.is_authorized:
            logger.error("Не авторизован")
            return []
        
        try:
            # Получение сущности канала
            channel_entity = await self.client.get_entity(channel_username)
            
            # Получение информации о канале
            channel_info = await self.client(functions.channels.GetFullChannelRequest(
                channel=channel_entity
            ))
            
            # Получение ключевых слов из описания канала
            description = channel_info.full_chat.about or ""
            keywords = [word.strip() for word in description.split() if len(word.strip()) > 3]
            
            # Поиск каналов по ключевым словам
            similar_channels = []
            
            for keyword in keywords[:5]:  # Используем первые 5 ключевых слов
                results = await self.client.search_global(keyword, limit=5)
                for result in results:
                    if isinstance(result.entity, Channel) and result.entity.id != channel_entity.id:
                        similar_channels.append(result.entity)
                        if len(similar_channels) >= limit:
                            break
                
                if len(similar_channels) >= limit:
                    break
            
            logger.info(f"Найдено {len(similar_channels)} похожих каналов для {channel_username}")
            return similar_channels
        except Exception as e:
            logger.error(f"Ошибка при поиске похожих каналов: {e}")
            return []
    
    async def filter_users(self, users, criteria=None):
        """
        Фильтрация пользователей по критериям
        
        Args:
            users (list): Список пользователей
            criteria (dict): Критерии фильтрации
            
        Returns:
            list: Отфильтрованный список пользователей
        """
        if not criteria:
            return users
        
        filtered_users = []
        
        for user in users:
            # Фильтрация по наличию фото профиля
            if criteria.get('has_photo') and not user.photo:
                continue
            
            # Фильтрация по времени последней активности
            if criteria.get('active_recently') and not user.status:
                continue
            
            # Фильтрация ботов
            if criteria.get('exclude_bots') and user.bot:
                continue
            
            # Фильтрация по языку (на основе имени пользователя или био)
            if criteria.get('language') and hasattr(user, 'about'):
                # Простая проверка на наличие кириллицы
                if criteria.get('language') == 'ru':
                    has_cyrillic = any(ord('а') <= ord(c) <= ord('я') for c in (user.about or '').lower())
                    if not has_cyrillic:
                        continue
            
            filtered_users.append(user)
        
        logger.info(f"Отфильтровано {len(filtered_users)} пользователей из {len(users)}")
        return filtered_users
    
    async def save_users_to_file(self, users, filename):
        """
        Сохранение списка пользователей в файл
        
        Args:
            users (list): Список пользователей
            filename (str): Имя файла
            
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        try:
            # Преобразование пользователей в словари
            user_dicts = []
            for user in users:
                user_dict = {
                    'id': user.id,
                    'access_hash': user.access_hash,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone if hasattr(user, 'phone') else None
                }
                user_dicts.append(user_dict)
            
            # Сохранение в файл
            with open(filename, 'w', encoding='utf-8') as file:
                yaml.dump(user_dicts, file)
            
            logger.info(f"Успешно сохранено {len(users)} пользователей в файл {filename}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователей в файл: {e}")
            return False
    
    async def load_users_from_file(self, filename):
        """
        Загрузка списка пользователей из файла
        
        Args:
            filename (str): Имя файла
            
        Returns:
            list: Список пользователей
        """
        try:
            # Загрузка из файла
            with open(filename, 'r', encoding='utf-8') as file:
                user_dicts = yaml.safe_load(file)
            
            # Преобразование словарей в объекты User
            users = []
            for user_dict in user_dicts:
                user = User(
                    id=user_dict['id'],
                    access_hash=user_dict['access_hash'],
                    username=user_dict.get('username'),
                    first_name=user_dict.get('first_name'),
                    last_name=user_dict.get('last_name'),
                    phone=user_dict.get('phone')
                )
                users.append(user)
            
            logger.info(f"Успешно загружено {len(users)} пользователей из файла {filename}")
            return users
        except Exception as e:
            logger.error(f"Ошибка при загрузке пользователей из файла: {e}")
            return []