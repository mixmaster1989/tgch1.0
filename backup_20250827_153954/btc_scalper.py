#!/usr/bin/env python3
"""
Скальпинговый модуль для BTC
- Анализирует BTC каждые 5 секунд
- Входит на 3 USDC при сигнале роста
- Фиксирует прибыль от 3 центов
- Быстрые входы и выходы
- РЫНОЧНЫЕ ОРДЕРА БЕЗ КОМИССИЙ (BTCUSDC)
"""

import asyncio
import time
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from decimal import Decimal

from mex_api import MexAPI
from technical_indicators import TechnicalIndicators
# from neural_analyzer import NeuralAnalyzer  # Убираем AI для скорости
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BTCScalper:
    """Скальпинговый модуль для BTC"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.tech_indicators = TechnicalIndicators()
        # self.neural_analyzer = NeuralAnalyzer()  # Убираем AI для скорости
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Настройки скальпинга - ПЕРЕВОД НА BTCUSDC!
        self.symbol = 'BTCUSDC'  # ИЗМЕНЕНО: BTCUSDT → BTCUSDC
        self.position_size_usdc = 4.9  # Размер позиции в USDC (увеличено с 3.0 до 4.9)
        self.min_profit_usdc = 0.003   # Минимальная прибыль (0.003 USDC = 3 цента)
        self.scan_interval = 5         # Сканирование каждые 5 секунд
        
        # Состояние позиции
        self.current_position = None   # Текущая открытая позиция
        self.entry_price = 0.0
        self.entry_time = None
        self.position_quantity = 0.0
        
        # Статистика
        self.total_trades = 0
        self.profitable_trades = 0
        self.total_profit = 0.0
        self.max_profit_trade = 0.0
        self.max_loss_trade = 0.0
        
        # Защита от частых операций
        self.last_trade_time = None
        self.min_trade_cooldown = 30   # Минимум 30 секунд между сделками
        
        # Флаг работы
        self.is_running = False
        
        # История цен для анализа
        self.price_history = []
        self.max_history_size = 100
        
        # Флаг для проверки баланса USDC
        self.last_balance_check = 0
        self.balance_check_interval = 300  # Проверяем баланс каждые 5 минут
        
        # Файл для сохранения состояния
        self.state_file = 'btc_scalper_state.json'
        
        # Загружаем сохраненное состояние при запуске
        self.load_state()
    
    def save_state(self):
        """Сохранить состояние в файл"""
        try:
            state = {
                'current_position': self.current_position,
                'entry_price': self.entry_price,
                'entry_time': self.entry_time,
                'position_quantity': self.position_quantity,
                'total_trades': self.total_trades,
                'profitable_trades': self.profitable_trades,
                'total_profit': self.total_profit,
                'max_profit_trade': self.max_profit_trade,
                'max_loss_trade': self.max_loss_trade,
                'last_trade_time': self.last_trade_time,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Состояние BTC скальпера сохранено: {self.state_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения состояния: {e}")
    
    def load_state(self):
        """Загрузить состояние из файла"""
        try:
            if not os.path.exists(self.state_file):
                logger.info("📁 Файл состояния не найден, начинаем с чистого листа")
                return
            
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Восстанавливаем состояние
            self.current_position = state.get('current_position')
            self.entry_price = state.get('entry_price', 0.0)
            self.entry_time = state.get('entry_time')
            self.position_quantity = state.get('position_quantity', 0.0)
            self.total_trades = state.get('total_trades', 0)
            self.profitable_trades = state.get('profitable_trades', 0)
            self.total_profit = state.get('total_profit', 0.0)
            self.max_profit_trade = state.get('max_profit_trade', 0.0)
            self.max_loss_trade = state.get('max_loss_trade', 0.0)
            self.last_trade_time = state.get('last_trade_time')
            
            saved_at = state.get('saved_at', 'неизвестно')
            logger.info(f"📂 Состояние BTC скальпера загружено из {self.state_file}")
            logger.info(f"📅 Сохранено: {saved_at}")
            
            if self.current_position:
                logger.info(f"📈 Восстановлена позиция: {self.position_quantity:.6f} BTC @ ${self.entry_price:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки состояния: {e}")
    
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
    
    def get_current_price(self) -> Optional[float]:
        """Получить текущую цену BTC"""
        try:
            ticker = self.mex_api.get_ticker_price(self.symbol)
            if ticker and 'price' in ticker:
                price = float(ticker['price'])
                self.update_price_history(price)
                return price
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены {self.symbol}: {e}")
            return None
    
    def update_price_history(self, price: float):
        """Обновить историю цен"""
        self.price_history.append({
            'price': price,
            'timestamp': time.time()
        })
        
        # Ограничиваем размер истории
        if len(self.price_history) > self.max_history_size:
            self.price_history.pop(0)
    
    def get_technical_analysis(self) -> Optional[Dict]:
        """Получить технический анализ BTC"""
        try:
            # Получаем свечи для анализа (1-минутные для скальпинга)
            klines = self.mex_api.get_klines(self.symbol, '1m', 50)
            if not klines or len(klines) < 20:
                return None
            
            # Рассчитываем технические индикаторы
            indicators = self.tech_indicators.calculate_all_indicators(klines, self.symbol)
            if not indicators:
                return None
            
            return indicators
            
        except Exception as e:
            logger.error(f"Ошибка технического анализа: {e}")
            return None
    
    # def get_ai_analysis(self) -> Optional[Dict]:
    #     """Получить AI анализ BTC - УБРАНО для скорости"""
    #     return None
    
    def calculate_scalping_signals(self, tech_analysis: Dict, ai_analysis: Dict = None) -> Dict:
        """Рассчитать скальпинговые сигналы"""
        try:
            signals = {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasons': [],
                'price': 0.0
            }
            
            current_price = self.get_current_price()
            if not current_price:
                return signals
            
            signals['price'] = current_price
            
            # Технические сигналы
            tech_signals = 0
            tech_reasons = []
            
            # RSI сигналы для скальпинга
            rsi = tech_analysis.get('rsi_14', 50)
            if rsi < 35:  # Перепроданность
                tech_signals += 2
                tech_reasons.append(f"RSI перепродан ({rsi:.1f})")
            elif rsi > 65:  # Перекупленность
                tech_signals -= 2
                tech_reasons.append(f"RSI перекуплен ({rsi:.1f})")
            
            # MACD сигналы
            macd_data = tech_analysis.get('macd', {})
            macd_histogram = macd_data.get('histogram', 0)
            if macd_histogram > 0:
                tech_signals += 1
                tech_reasons.append("MACD бычий")
            elif macd_histogram < 0:
                tech_signals -= 1
                tech_reasons.append("MACD медвежий")
            
            # Анализ тренда по MA
            sma_20 = tech_analysis.get('sma_20', current_price)
            ema_12 = tech_analysis.get('ema_12', current_price)
            
            if current_price > sma_20 and current_price > ema_12:
                tech_signals += 1
                tech_reasons.append("Цена выше MA")
            elif current_price < sma_20 and current_price < ema_12:
                tech_signals -= 1
                tech_reasons.append("Цена ниже MA")
            
            # Анализ объема
            volume_ratio = tech_analysis.get('volume_ratio', 1.0)
            if volume_ratio > 1.2:
                tech_signals += 1
                tech_reasons.append("Высокий объем")
            
            # AI сигналы - УБРАНО для скорости
            ai_signals = 0
            ai_reasons = []
            
            # Анализ краткосрочного тренда (последние 10 свечей)
            if len(self.price_history) >= 10:
                recent_prices = [p['price'] for p in self.price_history[-10:]]
                price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                if price_trend > 0.001:  # Рост более 0.1%
                    tech_signals += 1
                    tech_reasons.append("Краткосрочный рост")
                elif price_trend < -0.001:  # Падение более 0.1%
                    tech_signals -= 1
                    tech_reasons.append("Краткосрочное падение")
            
            # Объединяем сигналы
            total_signals = tech_signals + ai_signals
            all_reasons = tech_reasons + ai_reasons
            
            # Определяем действие - СНИЖАЕМ ПОРОГИ!
            if total_signals >= 1:  # Слабый сигнал покупки (было 3)
                signals['action'] = 'BUY'
                signals['confidence'] = min(0.9, 0.3 + (total_signals * 0.2))
            elif total_signals <= -1:  # Слабый сигнал продажи (было -3)
                signals['action'] = 'SELL'
                signals['confidence'] = min(0.9, 0.3 + (abs(total_signals) * 0.2))
            else:
                signals['action'] = 'HOLD'
                signals['confidence'] = 0.0
            
            signals['reasons'] = all_reasons
            
            return signals
            
        except Exception as e:
            logger.error(f"Ошибка расчета сигналов: {e}")
            return {'action': 'HOLD', 'confidence': 0.0, 'reasons': [], 'price': 0.0}
    
    def check_exit_conditions(self) -> bool:
        """Проверить условия выхода из позиции"""
        if not self.current_position:
            return False
        
        current_price = self.get_current_price()
        if not current_price:
            return False
        
        # ПРОСТЕЙШИЙ ФИЛЬТР: НЕ ПРОДАВАТЬ ДЕШЕВЛЕ ЦЕНЫ ПОКУПКИ!
        if self.current_position['side'] == 'BUY':
            # Если цена упала ниже цены покупки - НЕ ПРОДАЕМ!
            if current_price < self.entry_price:
                logger.info(f"🛡️ Цена ${current_price:.2f} < цены покупки ${self.entry_price:.2f} - НЕ ПРОДАЕМ!")
                return False
            
            # Продаем только если цена ВЫШЕ цены покупки
            pnl = (current_price - self.entry_price) * self.position_quantity
            if pnl >= self.min_profit_usdc:
                logger.info(f"🎯 Достигнута минимальная прибыль: ${pnl:.4f} USDC")
                return True
        else:
            # Для коротких позиций (если есть)
            if current_price > self.entry_price:
                logger.info(f"🛡️ Цена ${current_price:.2f} > цены продажи ${self.entry_price:.2f} - НЕ ПОКУПАЕМ!")
                return False
            
            pnl = (self.entry_price - current_price) * self.position_quantity
            if pnl >= self.min_profit_usdc:
                logger.info(f"🎯 Достигнута минимальная прибыль: ${pnl:.4f} USDC")
                return True
        
        # Проверяем убыток (стоп-лосс) - ТОЛЬКО ЕСЛИ ЦЕНА ВЫШЕ ПОКУПКИ
        if self.current_position['side'] == 'BUY' and current_price >= self.entry_price:
            max_loss = -self.min_profit_usdc * 2  # Максимальный убыток = 2x от минимальной прибыли
            if pnl <= max_loss:
                logger.warning(f"🛑 Достигнут максимальный убыток: ${pnl:.4f} USDC")
                return True
        
        return False
    
    def check_balance_periodically(self):
        """Периодическая проверка баланса USDC"""
        current_time = time.time()
        if current_time - self.last_balance_check > self.balance_check_interval:
            try:
                usdc_balance = self.get_usdc_balance()
                usdt_balance = self.get_usdt_balance()
                
                logger.info(f"💰 Баланс USDC: ${usdc_balance:.2f}, USDT: ${usdt_balance:.2f}")
                
                # Если USDC мало, но есть USDT - покупаем USDC
                if usdc_balance < 5.0 and usdt_balance > 10.0:
                    logger.info("🔄 Автоматическая покупка USDC за USDT...")
                    self.ensure_usdc_for_trade(5.0)
                
                self.last_balance_check = current_time
                
            except Exception as e:
                logger.error(f"❌ Ошибка проверки баланса: {e}")
    
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
    
    def ensure_usdc_for_trade(self, required_usdc: float) -> bool:
        """Убедиться, что есть USDC для сделки; при недостатке купить за USDT"""
        try:
            buffer = 0.02  # небольшой запас на комиссии
            need = required_usdc + buffer
            usdc_free = self.get_usdc_balance()
            
            if usdc_free >= need:
                return True

            # Покупаем недостающее количество USDC за USDT
            shortfall = max(0.0, need - usdc_free)
            usdt_free = self.get_usdt_balance()
            
            if usdt_free < shortfall:
                logger.warning(f"⚠️ Недостаточно USDT для покупки USDC: нужно ${shortfall:.2f}, есть ${usdt_free:.2f}")
                return False

            qty = round(shortfall, 2)
            if qty < 1.0:
                qty = 1.0  # минимальный разумный шаг

            # Покупаем USDC за USDT через рыночный ордер
            order = self.mex_api.place_order(
                symbol='USDCUSDT', 
                side='BUY', 
                quantity=qty
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Куплен USDC за USDT: ${qty:.2f}")
                try:
                    self.send_telegram_message(f"💱 Куплен USDC за USDT на ${qty:.2f} для сделки по {self.symbol}")
                except Exception:
                    pass
                return True
            else:
                logger.error(f"❌ Не удалось купить USDC: {order}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка ensure_usdc_for_trade: {e}")
            return False
    
    def get_usdt_balance(self) -> float:
        """Получить баланс USDT"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDT: {e}")
            return 0.0

    def execute_buy_order(self) -> bool:
        """Выполнить ордер покупки BTC за USDC"""
        try:
            current_price = self.get_current_price()
            if not current_price:
                return False
            
            # Убедимся, что хватает USDC для сделки
            if not self.ensure_usdc_for_trade(self.position_size_usdc):
                logger.error("❌ Недостаточно USDC для покупки BTC")
                return False
            
            # Рассчитываем количество BTC
            quantity = self.position_size_usdc / current_price
            quantity = round(quantity, 6)  # Округляем до 6 знаков
            
            # Размещаем РЫНОЧНЫЙ ордер (без комиссий!)
            order = self.mex_api.place_order(
                symbol=self.symbol,
                side='BUY',
                quantity=quantity
                # price=None означает рыночный ордер
            )
            
            if order and 'orderId' in order:
                # Обновляем состояние позиции
                self.current_position = {
                    'order_id': order['orderId'],
                    'side': 'BUY',
                    'quantity': quantity,
                    'price': current_price
                }
                self.entry_price = current_price
                self.entry_time = time.time()
                self.position_quantity = quantity
                
                # Сохраняем состояние после покупки
                self.save_state()
                
                logger.info(f"✅ Покупка BTC: {quantity:.6f} @ ${current_price:.2f} за {self.position_size_usdc} USDC")
                return True
            else:
                logger.error(f"❌ Ошибка покупки BTC: {order}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения покупки: {e}")
            return False
    
    def execute_sell_order(self) -> bool:
        """Выполнить ордер продажи BTC за USDC"""
        try:
            if not self.current_position:
                return False
            
            current_price = self.get_current_price()
            if not current_price:
                return False
            
            # Продаем всю позицию
            quantity = self.position_quantity
            
            # Размещаем РЫНОЧНЫЙ ордер (без комиссий!)
            order = self.mex_api.place_order(
                symbol=self.symbol,
                side='SELL',
                quantity=quantity
                # price=None означает рыночный ордер
            )
            
            if order and 'orderId' in order:
                # Рассчитываем P&L в USDC
                if self.current_position['side'] == 'BUY':
                    pnl = (current_price - self.entry_price) * quantity
                else:
                    pnl = (self.entry_price - current_price) * quantity
                
                # Обновляем статистику
                self.total_trades += 1
                if pnl > 0:
                    self.profitable_trades += 1
                    self.max_profit_trade = max(self.max_profit_trade, pnl)
                else:
                    self.max_loss_trade = min(self.max_loss_trade, pnl)
                
                self.total_profit += pnl
                
                # Сбрасываем позицию
                self.current_position = None
                self.entry_price = 0.0
                self.entry_time = None
                self.position_quantity = 0.0
                
                # Сохраняем состояние после продажи
                self.save_state()
                
                logger.info(f"✅ Продажа BTC: {quantity:.6f} @ ${current_price:.2f}, P&L: ${pnl:.4f} USDC")
                return True
            else:
                logger.error(f"❌ Ошибка продажи BTC: {order}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения продажи: {e}")
            return False
    
    def format_trade_report(self, action: str, signals: Dict, result: bool) -> str:
        """Форматировать отчет о сделке"""
        try:
            message = "<b>⚡ BTC СКАЛЬПЕР (BTCUSDC)</b>\n"
            message += "=" * 40 + "\n\n"
            
            message += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            message += f"💰 Цена BTC: ${signals['price']:.2f}\n"
            message += f"💱 Пара: {self.symbol}\n\n"
            
            message += "<b>🎯 СИГНАЛЫ:</b>\n"
            message += f"📊 Действие: {action}\n"
            if 'confidence' in signals:
                message += f"🎯 Уверенность: {signals['confidence']:.1%}\n"
            else:
                message += f"🎯 Уверенность: N/A (выход из позиции)\n"
            
            if 'reasons' in signals and signals['reasons']:
                message += f"📋 Причины: {', '.join(signals['reasons'])}\n"
            
            message += "\n<b>💼 РЕЗУЛЬТАТ:</b>\n"
            
            if result:
                if action == 'BUY':
                    message += "✅ Сделка выполнена\n"
                    message += f"📈 Позиция: {action}\n"
                    message += f"📊 Количество: {self.position_quantity:.6f} BTC\n"
                    message += f"💰 Цена входа: ${self.entry_price:.2f} USDC\n"
                    message += f"🛡️ ФИЛЬТР: НЕ ПРОДАЕМ ДЕШЕВЛЕ ${self.entry_price:.2f}!\n"
                    
                    # Рассчитываем время в позиции
                    if self.entry_time:
                        time_in_position = time.time() - self.entry_time
                        message += f"⏰ Время в позиции: {time_in_position:.0f} сек\n"
                    else:
                        message += "⏰ Время в позиции: 0 сек\n"
                else:
                    message += "✅ Сделка выполнена\n"
                    message += f"📉 Позиция: {action}\n"
                    message += f"📊 Количество: {self.position_quantity:.6f} BTC\n"
                    message += f"💰 Цена выхода: ${self.entry_price:.2f} USDC\n"
                    
                    # Показываем PnL
                    if self.current_position and 'entry_price' in self.current_position:
                        entry_price = self.current_position['entry_price']
                        pnl = (self.entry_price - entry_price) * self.position_quantity
                        message += f"📈 PnL: ${pnl:.4f} USDC\n"
            else:
                message += "❌ Сделка не выполнена\n"
                if action == 'BUY':
                    message += "💡 Возможные причины:\n"
                    message += "   - Недостаточно USDC\n"
                    message += "   - Ошибка API\n"
                    message += "   - Недостаточная ликвидность\n"
                else:
                    message += "💡 Возможные причины:\n"
                    message += "   - Цена ниже цены покупки (фильтр защиты)\n"
                    message += "   - Недостаточная прибыль\n"
                    message += "   - Ошибка API\n"
            
            message += "\n" + "=" * 40 + "\n"
            message += "<b>⚡ BTC СКАЛЬПЕР</b>"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования отчета: {e}")
            return f"❌ Ошибка отчета: {e}"
    
    def format_statistics_report(self) -> str:
        """Форматировать отчет статистики"""
        try:
            win_rate = (self.profitable_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            message = "<b>📊 BTC СКАЛЬПЕР - СТАТИСТИКА (BTCUSDC)</b>\n"
            message += "=" * 40 + "\n\n"
            
            message += f"📈 Всего сделок: {self.total_trades}\n"
            message += f"✅ Прибыльных: {self.profitable_trades}\n"
            message += f"📊 Винрейт: {win_rate:.1f}%\n"
            message += f"💰 Общая прибыль: ${self.total_profit:.4f} USDC\n"
            message += f"📈 Макс. прибыль: ${self.max_profit_trade:.4f} USDC\n"
            message += f"📉 Макс. убыток: ${self.max_loss_trade:.4f} USDC\n"
            
            if self.total_trades > 0:
                avg_profit = self.total_profit / self.total_trades
                message += f"📊 Средняя прибыль: ${avg_profit:.4f} USDC\n"
            
            message += f"\n💱 Торговая пара: {self.symbol}\n"
            message += f"💰 Размер позиции: ${self.position_size_usdc:.2f} USDC\n"
            message += f"🎯 Мин. прибыль: ${self.min_profit_usdc:.3f} USDC\n"
            
            message += "\n" + "=" * 40 + "\n"
            message += "<b>📊 BTC СКАЛЬПЕР (BTCUSDC)</b>"
            
            return message
            
        except Exception as e:
            return f"❌ Ошибка форматирования статистики: {e}"
    
    async def scalping_cycle(self):
        """Один цикл скальпинга"""
        try:
            # Периодическая проверка баланса
            self.check_balance_periodically()
            
            # Проверяем кулдаун между сделками
            if (self.last_trade_time and 
                time.time() - self.last_trade_time < self.min_trade_cooldown):
                return
            
            # Если есть открытая позиция, проверяем условия выхода
            if self.current_position:
                if self.check_exit_conditions():
                    result = self.execute_sell_order()
                    if result:
                        self.last_trade_time = time.time()
                        report = self.format_trade_report("EXIT", {'price': self.get_current_price() or 0}, result)
                        self.send_telegram_message(report)
                return
            
            # Получаем технический анализ
            tech_analysis = self.get_technical_analysis()
            if not tech_analysis:
                logger.warning("❌ Не удалось получить технический анализ")
                return
            
            # Рассчитываем сигналы (только технические индикаторы)
            signals = self.calculate_scalping_signals(tech_analysis)
            
            # Логируем каждый сканирование
            current_price = signals.get('price', 0)
            rsi = tech_analysis.get('rsi_14', 50)
            macd_hist = tech_analysis.get('macd', {}).get('histogram', 0)
            
            logger.info(f"🔍 BTC Сканирование: ${current_price:.2f} | RSI: {rsi:.1f} | MACD: {macd_hist:.2f} | Сигнал: {signals['action']} ({signals['confidence']:.1%})")
            
            # Проверяем сигнал на покупку - СНИЖАЕМ ПОРОГ!
            if signals['action'] == 'BUY' and signals['confidence'] > 0.3:  # Было 0.6
                logger.info(f"🎯 СИГНАЛ ПОКУПКИ BTC: {signals['confidence']:.1%} | Причины: {', '.join(signals['reasons'])}")
                
                result = self.execute_buy_order()
                if result:
                    self.last_trade_time = time.time()
                    report = self.format_trade_report("BUY", signals, result)
                    self.send_telegram_message(report)
            
        except Exception as e:
            logger.error(f"❌ Ошибка цикла скальпинга: {e}")
    
    async def start_scalping(self):
        """Запустить скальпинг"""
        logger.info("🚀 Запуск BTC скальпера")
        logger.info(f"📊 Настройки:")
        logger.info(f"   Символ: {self.symbol}")
        logger.info(f"   Размер позиции: ${self.position_size_usdc}")
        logger.info(f"   Минимальная прибыль: ${self.min_profit_usdc}")
        logger.info(f"   Интервал сканирования: {self.scan_interval} сек")
        
        self.is_running = True
        
        while self.is_running:
            try:
                await self.scalping_cycle()
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"❌ Критическая ошибка скальпинга: {e}")
                await asyncio.sleep(self.scan_interval)
    
    def stop_scalping(self):
        """Остановить скальпинг"""
        logger.info("🛑 Остановка BTC скальпера")
        self.is_running = False
        
        # Закрываем открытую позицию при остановке
        if self.current_position:
            logger.info("🔄 Закрытие открытой позиции...")
            self.execute_sell_order()
    
    def get_status(self) -> Dict:
        """Получить статус скальпера"""
        return {
            'is_running': self.is_running,
            'current_position': self.current_position,
            'total_trades': self.total_trades,
            'profitable_trades': self.profitable_trades,
            'total_profit': self.total_profit,
            'max_profit_trade': self.max_profit_trade,
            'max_loss_trade': self.max_loss_trade,
            'scan_interval': self.scan_interval,
            'position_size_usdc': self.position_size_usdc,
            'min_profit_usdc': self.min_profit_usdc
        }

# Функция для запуска в отдельном потоке
def run_btc_scalper():
    """Запустить BTC скальпер в отдельном потоке"""
    scalper = BTCScalper()
    asyncio.run(scalper.start_scalping())

if __name__ == "__main__":
    # Тестовый запуск
    scalper = BTCScalper()
    asyncio.run(scalper.start_scalping())
