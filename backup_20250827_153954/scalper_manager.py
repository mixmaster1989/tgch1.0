#!/usr/bin/env python3
"""
Менеджер скальперов - управление множественными экземплярами BTC/ETH скальперов
Решает проблему "застревания" скальперов при просадках цен
"""

import asyncio
import time
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScalperStatus(Enum):
    """Статусы скальпера"""
    IDLE = "idle"           # Ожидает сигнала
    ACTIVE = "active"       # Активно торгует
    STUCK = "stuck"         # Застрял (цена ниже точки входа)
    PROFIT = "profit"       # Закрыл с прибылью
    LOSS = "loss"          # Закрыл с убытком

@dataclass
class ScalperInstance:
    """Экземпляр скальпера"""
    id: str                    # Уникальный ID
    symbol: str               # Торговая пара (BTCUSDC/ETHUSDC)
    status: ScalperStatus     # Текущий статус
    entry_price: float        # Цена входа
    entry_time: datetime      # Время входа
    position_size: float      # Размер позиции в USDC
    current_quantity: float   # Текущее количество актива
    stuck_since: Optional[datetime] = None  # Когда застрял
    profit_target: float = 0.02  # Целевая прибыль в USDC (2 цента)
    max_stuck_time: int = 86400   # Максимальное время "застревания" (24 часа)

class ScalperManager:
    """Менеджер скальперов для управления множественными экземплярами"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Настройки менеджера
        self.scan_interval = 30  # Проверка каждые 30 секунд
        self.max_instances_per_symbol = 3  # Максимум 3 экземпляра на символ
        self.min_stuck_time = 86400  # Минимум 24 часа (сутки) "застревания" перед запуском нового
        
        # ЗАЩИТА БАЛАНСА USDC - УВЕЛИЧЕНО ДО $20!
        self.min_usdc_balance_after_scalper = 5.0  # Минимум $5 USDC должно остаться для скальперов
        self.position_size_usdc = 4.9  # Размер позиции каждого скальпера
        
        # Активные экземпляры скальперов
        self.btc_scalpers: List[ScalperInstance] = []
        self.eth_scalpers: List[ScalperInstance] = []
        
        # Статистика
        self.total_instances_created = 0
        self.total_instances_closed = 0
        self.total_profit = 0.0
        
        # Флаг работы
        self.is_running = False
        
        # Файл для сохранения состояния
        self.state_file = 'scalper_manager_state.json'
        
        # Загружаем сохраненное состояние
        self.load_state()
    
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        if not self.bot_token or not self.chat_id:
            return
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_usdc_balance(self) -> float:
        """Получить баланс USDC"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'USDC':
                    return float(balance['free'])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDC: {e}")
            return 0.0
    
    def get_current_price(self, symbol: str) -> float:
        """Получить текущую цену символа"""
        try:
            ticker = self.mex_api.get_ticker_price(symbol)
            if 'price' in ticker:
                return float(ticker['price'])
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}")
            return 0.0
    
    def can_create_new_scalper(self, symbol: str) -> Tuple[bool, str]:
        """Проверить, можно ли создать новый скальпер"""
        try:
            # Проверяем количество активных экземпляров
            active_scalpers = self.get_active_scalpers(symbol)
            if len(active_scalpers) >= self.max_instances_per_symbol:
                return False, f"Достигнут лимит экземпляров для {symbol}"
            
            # Проверяем баланс USDC
            current_usdc = self.get_usdc_balance()
            required_usdc = self.position_size_usdc
            remaining_after = current_usdc - required_usdc
            
            if remaining_after < self.min_usdc_balance_after_scalper:
                return False, f"Недостаточно USDC: останется ${remaining_after:.2f}, нужно минимум ${self.min_usdc_balance_after_scalper:.2f}"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Ошибка проверки возможности создания скальпера: {e}")
            return False, f"Ошибка: {e}"
    
    def create_scalper_instance(self, symbol: str, entry_price: float) -> Optional[ScalperInstance]:
        """Создать новый экземпляр скальпера"""
        try:
            can_create, reason = self.can_create_new_scalper(symbol)
            if not can_create:
                logger.warning(f"❌ Нельзя создать скальпер {symbol}: {reason}")
                return None
            
            # Создаем новый экземпляр
            instance_id = f"{symbol}_{int(time.time())}"
            instance = ScalperInstance(
                id=instance_id,
                symbol=symbol,
                status=ScalperStatus.ACTIVE,
                entry_price=entry_price,
                entry_time=datetime.now(),
                position_size=self.position_size_usdc,
                current_quantity=self.position_size_usdc / entry_price
            )
            
            # Добавляем в соответствующий список
            if symbol == 'BTCUSDC':
                self.btc_scalpers.append(instance)
            elif symbol == 'ETHUSDC':
                self.eth_scalpers.append(instance)
            
            self.total_instances_created += 1
            
            # Отправляем уведомление
            message = f"🚀 <b>Создан новый скальпер</b>\n" \
                     f"Символ: {symbol}\n" \
                     f"Цена входа: ${entry_price:.2f}\n" \
                     f"Размер: ${self.position_size_usdc:.2f} USDC\n" \
                     f"ID: {instance_id}"
            self.send_telegram_message(message)
            
            logger.info(f"✅ Создан новый скальпер {symbol} @ ${entry_price:.2f}")
            return instance
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания скальпера {symbol}: {e}")
            return None
    
    def get_active_scalpers(self, symbol: str) -> List[ScalperInstance]:
        """Получить активные экземпляры скальпера для символа"""
        if symbol == 'BTCUSDC':
            return [s for s in self.btc_scalpers if s.status in [ScalperStatus.ACTIVE, ScalperStatus.STUCK]]
        elif symbol == 'ETHUSDC':
            return [s for s in self.eth_scalpers if s.status in [ScalperStatus.ACTIVE, ScalperStatus.STUCK]]
        return []
    
    def update_scalper_status(self, instance: ScalperInstance, current_price: float):
        """Обновить статус скальпера на основе текущей цены"""
        try:
            if instance.status == ScalperStatus.ACTIVE:
                # Проверяем, не застрял ли скальпер
                if current_price < instance.entry_price:
                    if instance.stuck_since is None:
                        instance.stuck_since = datetime.now()
                        instance.status = ScalperStatus.STUCK
                        logger.info(f"⚠️ Скальпер {instance.id} застрял @ ${current_price:.2f} < ${instance.entry_price:.2f}")
                
                # Проверяем прибыль (только для мониторинга, не закрываем позицию)
                profit = (current_price - instance.entry_price) * instance.current_quantity
                if profit >= instance.profit_target:
                    logger.info(f"💰 Скальпер {instance.id} достиг целевой прибыли ${profit:.3f} (мониторинг)")
                    # НЕ отправляем уведомление - это ложное "закрытие"
            
            elif instance.status == ScalperStatus.STUCK:
                # Проверяем, вернулась ли цена к точке входа
                if current_price >= instance.entry_price:
                    instance.status = ScalperStatus.ACTIVE
                    instance.stuck_since = None
                    logger.info(f"✅ Скальпер {instance.id} разблокирован @ ${current_price:.2f}")
                    
                    # Отправляем уведомление
                    message = f"✅ <b>Скальпер разблокирован</b>\n" \
                             f"Символ: {instance.symbol}\n" \
                             f"Цена: ${current_price:.2f}\n" \
                             f"ID: {instance.id}"
                    self.send_telegram_message(message)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статуса скальпера {instance.id}: {e}")
    
    def should_create_new_scalper(self, symbol: str) -> bool:
        """Определить, нужно ли создать новый скальпер"""
        try:
            active_scalpers = self.get_active_scalpers(symbol)
            
            # Если нет активных скальперов, создаем
            if not active_scalpers:
                return True
            
            # Проверяем, есть ли застрявшие скальперы
            stuck_scalpers = [s for s in active_scalpers if s.status == ScalperStatus.STUCK]
            
            for stuck_scalper in stuck_scalpers:
                if stuck_scalper.stuck_since:
                    stuck_duration = (datetime.now() - stuck_scalper.stuck_since).total_seconds()
                    if stuck_duration >= self.min_stuck_time:
                        hours_stuck = stuck_duration / 3600
                        
                        # Создаем новый скальпер, если существующий застрял на 24+ часа
                        if stuck_scalper.id.startswith(f"{symbol}_existing_"):
                            logger.info(f"⏰ Существующий скальпер {stuck_scalper.id} застрял на {hours_stuck:.1f} часов (24+ часов), СОЗДАЕМ НОВЫЙ")
                            return True
                        else:
                            logger.info(f"⏰ Скальпер {stuck_scalper.id} застрял на {hours_stuck:.1f} часов (24+ часов), создаем новый")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки необходимости создания скальпера: {e}")
            return False
    
    def cleanup_closed_scalpers(self):
        """Очистить закрытые скальперы из списков"""
        try:
            # Очищаем BTC скальперы
            self.btc_scalpers = [s for s in self.btc_scalpers 
                               if s.status not in [ScalperStatus.PROFIT, ScalperStatus.LOSS]]
            
            # Очищаем ETH скальперы
            self.eth_scalpers = [s for s in self.eth_scalpers 
                               if s.status not in [ScalperStatus.PROFIT, ScalperStatus.LOSS]]
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки закрытых скальперов: {e}")
    
    def get_manager_status(self) -> Dict:
        """Получить статус менеджера"""
        try:
            btc_active = len([s for s in self.btc_scalpers if s.status == ScalperStatus.ACTIVE])
            btc_stuck = len([s for s in self.btc_scalpers if s.status == ScalperStatus.STUCK])
            eth_active = len([s for s in self.eth_scalpers if s.status == ScalperStatus.ACTIVE])
            eth_stuck = len([s for s in self.eth_scalpers if s.status == ScalperStatus.STUCK])
            
            # Подсчитываем существующие скальперы
            btc_existing = len([s for s in self.btc_scalpers if s.id.startswith('BTCUSDC_existing_')])
            eth_existing = len([s for s in self.eth_scalpers if s.id.startswith('ETHUSDC_existing_')])
            
            return {
                'btc_active': btc_active,
                'btc_stuck': btc_stuck,
                'eth_active': eth_active,
                'eth_stuck': eth_stuck,
                'btc_existing': btc_existing,
                'eth_existing': eth_existing,
                'total_created': self.total_instances_created,
                'total_profit': self.total_profit,
                'usdc_balance': self.get_usdc_balance()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса менеджера: {e}")
            return {}
    
    def get_existing_scalpers_info(self) -> Dict:
        """Получить подробную информацию о существующих скальперах"""
        try:
            existing_info = {
                'btc_existing': [],
                'eth_existing': []
            }
            
            # Информация о существующих BTC скальперах
            for scalper in self.btc_scalpers:
                if scalper.id.startswith('BTCUSDC_existing_'):
                    info = {
                        'id': scalper.id,
                        'entry_price': scalper.entry_price,
                        'entry_time': scalper.entry_time.isoformat(),
                        'position_size': scalper.position_size,
                        'current_quantity': scalper.current_quantity,
                        'status': scalper.status.value,
                        'stuck_since': scalper.stuck_since.isoformat() if scalper.stuck_since else None
                    }
                    existing_info['btc_existing'].append(info)
            
            # Информация о существующих ETH скальперах
            for scalper in self.eth_scalpers:
                if scalper.id.startswith('ETHUSDC_existing_'):
                    info = {
                        'id': scalper.id,
                        'entry_price': scalper.entry_price,
                        'entry_time': scalper.entry_time.isoformat(),
                        'position_size': scalper.position_size,
                        'current_quantity': scalper.current_quantity,
                        'status': scalper.status.value,
                        'stuck_since': scalper.stuck_since.isoformat() if scalper.stuck_since else None
                    }
                    existing_info['eth_existing'].append(info)
            
            return existing_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о существующих скальперах: {e}")
            return {'btc_existing': [], 'eth_existing': []}
    
    def save_state(self):
        """Сохранить состояние менеджера"""
        try:
            # Кастомная сериализация для правильного сохранения enum
            def serialize_scalper(scalper):
                data = asdict(scalper)
                data['status'] = scalper.status.value  # Сохраняем значение enum, а не объект
                data['entry_time'] = scalper.entry_time.isoformat()
                if scalper.stuck_since:
                    data['stuck_since'] = scalper.stuck_since.isoformat()
                return data
            
            state = {
                'btc_scalpers': [serialize_scalper(s) for s in self.btc_scalpers],
                'eth_scalpers': [serialize_scalper(s) for s in self.eth_scalpers],
                'total_instances_created': self.total_instances_created,
                'total_profit': self.total_profit,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Состояние менеджера скальперов сохранено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения состояния: {e}")
    
    def load_state(self):
        """Загрузить состояние менеджера"""
        try:
            if not os.path.exists(self.state_file):
                logger.info("📁 Файл состояния менеджера не найден, начинаем с чистого листа")
                # Загружаем существующие скальперы при первом запуске
                self.load_existing_scalpers()
                return
            
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Восстанавливаем BTC скальперы
            self.btc_scalpers = []
            for s_data in state.get('btc_scalpers', []):
                # Исправляем загрузку статуса enum
                status_str = s_data['status']
                if status_str.startswith('ScalperStatus.'):
                    status_str = status_str.split('.')[1].lower()
                status = ScalperStatus(status_str)
                
                instance = ScalperInstance(
                    id=s_data['id'],
                    symbol=s_data['symbol'],
                    status=status,
                    entry_price=s_data['entry_price'],
                    entry_time=datetime.fromisoformat(s_data['entry_time']),
                    position_size=s_data['position_size'],
                    current_quantity=s_data['current_quantity'],
                    stuck_since=datetime.fromisoformat(s_data['stuck_since']) if s_data.get('stuck_since') else None,
                    profit_target=s_data.get('profit_target', 0.02),
                    max_stuck_time=s_data.get('max_stuck_time', 86400)
                )
                self.btc_scalpers.append(instance)
            
            # Восстанавливаем ETH скальперы
            self.eth_scalpers = []
            for s_data in state.get('eth_scalpers', []):
                # Исправляем загрузку статуса enum
                status_str = s_data['status']
                if status_str.startswith('ScalperStatus.'):
                    status_str = status_str.split('.')[1].lower()
                status = ScalperStatus(status_str)
                
                instance = ScalperInstance(
                    id=s_data['id'],
                    symbol=s_data['symbol'],
                    status=status,
                    entry_price=s_data['entry_price'],
                    entry_time=datetime.fromisoformat(s_data['entry_time']),
                    position_size=s_data['position_size'],
                    current_quantity=s_data['current_quantity'],
                    stuck_since=datetime.fromisoformat(s_data['stuck_since']) if s_data.get('stuck_since') else None,
                    profit_target=s_data.get('profit_target', 0.02),
                    max_stuck_time=s_data.get('max_stuck_time', 86400)
                )
                self.eth_scalpers.append(instance)
            
            self.total_instances_created = state.get('total_instances_created', 0)
            self.total_profit = state.get('total_profit', 0.0)
            
            logger.info(f"📂 Состояние менеджера скальперов загружено")
            logger.info(f"📊 BTC: {len(self.btc_scalpers)} экземпляров, ETH: {len(self.eth_scalpers)} экземпляров")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки состояния: {e}")
    
    def load_existing_scalpers(self):
        """Загрузить существующие скальперы из их файлов состояния"""
        try:
            logger.info("🔍 Загрузка существующих скальперов...")
            
            # Загружаем BTC скальпер
            btc_state_file = 'btc_scalper_state.json'
            if os.path.exists(btc_state_file):
                with open(btc_state_file, 'r', encoding='utf-8') as f:
                    btc_state = json.load(f)
                
                if btc_state.get('current_position') and btc_state.get('entry_price'):
                    entry_time = datetime.fromtimestamp(btc_state.get('entry_time', time.time()))
                    
                    # Проверяем, застрял ли скальпер (если прошло больше 24 часов)
                    current_time = datetime.now()
                    age_hours = (current_time - entry_time).total_seconds() / 3600
                    is_stuck = age_hours >= 24  # Если скальпер старше 24 часов, считаем застрявшим
                    
                    instance = ScalperInstance(
                        id=f"BTCUSDC_existing_{int(entry_time.timestamp())}",
                        symbol='BTCUSDC',
                        status=ScalperStatus.STUCK if is_stuck else ScalperStatus.ACTIVE,
                        entry_price=btc_state['entry_price'],
                        entry_time=entry_time,
                        position_size=btc_state.get('position_quantity', 0) * btc_state['entry_price'],
                        current_quantity=btc_state.get('position_quantity', 0),
                        stuck_since=entry_time if is_stuck else None  # Устанавливаем время застревания
                    )
                    self.btc_scalpers.append(instance)
                    logger.info(f"📂 Загружен существующий BTC скальпер: {instance.id} @ ${instance.entry_price:.2f} (возраст: {age_hours:.1f}ч, {'застрял' if is_stuck else 'активен'})")
            
            # Загружаем ETH скальпер
            eth_state_file = 'eth_scalper_state.json'
            if os.path.exists(eth_state_file):
                with open(eth_state_file, 'r', encoding='utf-8') as f:
                    eth_state = json.load(f)
                
                if eth_state.get('current_position') and eth_state.get('entry_price'):
                    entry_time = datetime.fromtimestamp(eth_state.get('entry_time', time.time()))
                    
                    # Проверяем, застрял ли скальпер (если прошло больше 24 часов)
                    current_time = datetime.now()
                    age_hours = (current_time - entry_time).total_seconds() / 3600
                    is_stuck = age_hours >= 24  # Если скальпер старше 24 часов, считаем застрявшим
                    
                    instance = ScalperInstance(
                        id=f"ETHUSDC_existing_{int(entry_time.timestamp())}",
                        symbol='ETHUSDC',
                        status=ScalperStatus.STUCK if is_stuck else ScalperStatus.ACTIVE,
                        entry_price=eth_state['entry_price'],
                        entry_time=entry_time,
                        position_size=eth_state.get('position_quantity', 0) * eth_state['entry_price'],
                        current_quantity=eth_state.get('position_quantity', 0),
                        stuck_since=entry_time if is_stuck else None  # Устанавливаем время застревания
                    )
                    self.eth_scalpers.append(instance)
                    logger.info(f"📂 Загружен существующий ETH скальпер: {instance.id} @ ${instance.entry_price:.2f} (возраст: {age_hours:.1f}ч, {'застрял' if is_stuck else 'активен'})")
            
            total_existing = len(self.btc_scalpers) + len(self.eth_scalpers)
            logger.info(f"✅ Загружено {total_existing} существующих скальперов")
            
            # Отправляем уведомление о загруженных скальперах
            if total_existing > 0:
                message = f"📂 <b>Загружены существующие скальперы</b>\n" \
                         f"BTC: {len(self.btc_scalpers)} экземпляров\n" \
                         f"ETH: {len(self.eth_scalpers)} экземпляров\n" \
                         f"Менеджер будет отслеживать их без перезапуска"
                self.send_telegram_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки существующих скальперов: {e}")
    
    def check_existing_scalper_status(self, symbol: str, current_price: float) -> bool:
        """Проверить статус существующего скальпера и обновить его"""
        try:
            scalpers = self.btc_scalpers if symbol == 'BTCUSDC' else self.eth_scalpers
            
            for scalper in scalpers:
                if scalper.id.startswith(f"{symbol}_existing_"):
                    # Обновляем статус существующего скальпера
                    self.update_scalper_status(scalper, current_price)
                    
                    # Если скальпер застрял, логируем это
                    if scalper.status == ScalperStatus.STUCK:
                        if scalper.stuck_since:
                            stuck_duration = (datetime.now() - scalper.stuck_since).total_seconds()
                            hours_stuck = stuck_duration / 3600
                            logger.info(f"⚠️ Существующий скальпер {scalper.id} застрял на {hours_stuck:.1f} часов @ ${current_price:.2f} < ${scalper.entry_price:.2f}")
                    
                    return True  # Найден существующий скальпер
            
            return False  # Существующий скальпер не найден
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса существующего скальпера: {e}")
            return False
    
    async def run(self):
        """Основной цикл работы менеджера"""
        try:
            self.is_running = True
            logger.info("🚀 Менеджер скальперов запущен")
            
            # Отправляем уведомление о запуске
            message = f"🚀 <b>Менеджер скальперов запущен</b>\n" \
                     f"Защита баланса: ${self.min_usdc_balance_after_scalper:.2f} USDC\n" \
                     f"Размер позиции: ${self.position_size_usdc:.2f} USDC\n" \
                     f"Максимум экземпляров: {self.max_instances_per_symbol} на символ"
            self.send_telegram_message(message)
            
            while self.is_running:
                try:
                    # Получаем текущие цены
                    btc_price = self.get_current_price('BTCUSDC')
                    eth_price = self.get_current_price('ETHUSDC')
                    
                    if btc_price > 0 and eth_price > 0:
                        # Проверяем существующие скальперы
                        btc_has_existing = self.check_existing_scalper_status('BTCUSDC', btc_price)
                        eth_has_existing = self.check_existing_scalper_status('ETHUSDC', eth_price)
                        
                        # Обновляем статусы всех скальперов
                        for scalper in self.btc_scalpers + self.eth_scalpers:
                            current_price = btc_price if scalper.symbol == 'BTCUSDC' else eth_price
                            self.update_scalper_status(scalper, current_price)
                        
                        # Проверяем необходимость создания новых скальперов
                        # Создаем новые, если существующие застряли на 24+ часа
                        if self.should_create_new_scalper('BTCUSDC'):
                            self.create_scalper_instance('BTCUSDC', btc_price)
                        
                        if self.should_create_new_scalper('ETHUSDC'):
                            self.create_scalper_instance('ETHUSDC', eth_price)
                        
                        # Очищаем закрытые скальперы
                        self.cleanup_closed_scalpers()
                        
                        # Сохраняем состояние каждые 5 минут
                        if int(time.time()) % 300 < self.scan_interval:
                            self.save_state()
                    
                    # Ждем следующей итерации
                    await asyncio.sleep(self.scan_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка в цикле менеджера: {e}")
                    await asyncio.sleep(self.scan_interval)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка менеджера: {e}")
        finally:
            self.is_running = False
            logger.info("🛑 Менеджер скальперов остановлен")
    
    def stop(self):
        """Остановить менеджер"""
        self.is_running = False
        self.save_state()
        logger.info("🛑 Менеджер скальперов остановлен")

# Функция для получения защищенного баланса USDC для скальперов
def get_scalper_protected_balance() -> float:
    """Получить защищенный баланс USDC для скальперов"""
    try:
        manager = ScalperManager()
        current_usdc = manager.get_usdc_balance()
        protected_balance = current_usdc - manager.min_usdc_balance_after_scalper
        return max(0.0, protected_balance)
    except Exception as e:
        logger.error(f"❌ Ошибка получения защищенного баланса: {e}")
        return 0.0

# Функция для проверки возможности создания скальпера
def can_create_scalper(symbol: str) -> Tuple[bool, str]:
    """Проверить, можно ли создать скальпер для символа"""
    try:
        manager = ScalperManager()
        return manager.can_create_new_scalper(symbol)
    except Exception as e:
        logger.error(f"❌ Ошибка проверки возможности создания скальпера: {e}")
        return False, f"Ошибка: {e}"
