#!/usr/bin/env python3
"""
Scalpers Reporter
- Отчеты по BTC и ETH скальперам
- Фильтрация по размеру позиции (≤$5)
- Исключение ордеров основного портфеля
- Отчеты каждые 10 минут и при перезапуске
"""

import time
import logging
from datetime import datetime
from typing import Dict, List
import threading

from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from scalper_manager import ScalperManager
import requests

logger = logging.getLogger(__name__)

class ScalpersReporter:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.report_interval_sec = 600  # 10 минут
        self.max_position_size = 5.0  # Максимальный размер позиции скальпера ($5)
        self.start_time_ms = 1756107900000  # 11:25 по Москве (25.08.2025) - игнорируем тесты до этой даты
        
        # Флаг работы
        self.is_running = False
        
        # Интеграция с менеджером скальперов
        self.scalper_manager = ScalperManager()
        
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
    
    def get_scalper_orders(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Получить ордера скальпера (фильтрация по размеру ≤$5)"""
        try:
            orders = self.mex_api.get_order_history(symbol, limit=limit)
            if not orders:
                return []
            
            # Фильтруем только ордера скальперов (размер ≤$5 и время ≥ 11:25)
            scalper_orders = []
            for order in orders:
                if order.get('status') == 'FILLED':
                    quote_qty = float(order.get('cummulativeQuoteQty', 0))
                    order_time = order.get('time', 0)
                    if quote_qty <= self.max_position_size and order_time >= self.start_time_ms:
                        scalper_orders.append(order)
            
            return scalper_orders
            
        except Exception as e:
            logger.error(f"Ошибка получения ордеров {symbol}: {e}")
            return []
    
    def calculate_real_price(self, order: Dict) -> float:
        """Рассчитать реальную цену исполнения ордера"""
        try:
            # Для рыночных ордеров используем реальную цену исполнения
            executed_qty = float(order.get('executedQty', 0))
            cummulative_quote_qty = float(order.get('cummulativeQuoteQty', 0))
            
            if executed_qty > 0:
                # Реальная цена = общая сумма в USDC / количество исполненных монет
                real_price = cummulative_quote_qty / executed_qty
                return real_price
            else:
                # Fallback на цену ордера
                return float(order.get('price', 0))
                
        except Exception as e:
            logger.error(f"Ошибка расчета реальной цены: {e}")
            return float(order.get('price', 0))
    
    def get_manager_scalpers_data(self, symbol: str) -> Dict:
        """Получить данные скальперов от менеджера"""
        try:
            # Загружаем состояние менеджера
            self.scalper_manager.load_state()
            
            # Получаем скальперы для символа
            if symbol == 'BTCUSDC':
                scalpers = self.scalper_manager.btc_scalpers
            elif symbol == 'ETHUSDC':
                scalpers = self.scalper_manager.eth_scalpers
            else:
                return {}
            
            # Фильтруем только новые скальперы (не существующие)
            new_scalpers = [s for s in scalpers if not s.id.startswith(f'{symbol}_existing_')]
            
            return {
                'total_scalpers': len(new_scalpers),
                'active_scalpers': len([s for s in new_scalpers if s.status.value == 'active']),
                'stuck_scalpers': len([s for s in new_scalpers if s.status.value == 'stuck']),
                'profit_scalpers': len([s for s in new_scalpers if s.status.value == 'profit']),
                'total_profit': sum([s.profit_target for s in new_scalpers if s.status.value == 'profit']),
                'scalpers': new_scalpers
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения данных менеджера для {symbol}: {e}")
            return {}
    
    def analyze_scalper_performance(self, symbol: str) -> Dict:
        """Анализ производительности скальпера"""
        try:
            orders = self.get_scalper_orders(symbol)
            if not orders:
                return {
                    'symbol': symbol,
                    'total_trades': 0,
                    'profitable_trades': 0,
                    'total_pnl': 0.0,
                    'max_profit': 0.0,
                    'max_loss': 0.0,
                    'avg_profit': 0.0,
                    'win_rate': 0.0,
                    'trades': []
                }
            
            # Группируем ордера по парам (покупка + продажа)
            trades = []
            buy_orders = []
            sell_orders = []
            
            for order in orders:
                if order['side'] == 'BUY':
                    buy_orders.append(order)
                elif order['side'] == 'SELL':
                    sell_orders.append(order)
            
            # Сортируем по времени
            buy_orders.sort(key=lambda x: x['time'])
            sell_orders.sort(key=lambda x: x['time'])
            
            # Сопоставляем покупки и продажи
            for i, buy_order in enumerate(buy_orders):
                if i < len(sell_orders):
                    sell_order = sell_orders[i]
                    
                    # Используем реальные цены исполнения
                    buy_price = self.calculate_real_price(buy_order)
                    sell_price = self.calculate_real_price(sell_order)
                    quantity = float(buy_order['executedQty'])
                    
                    # PnL = (sell_price - buy_price) * quantity
                    pnl = (sell_price - buy_price) * quantity
                    
                    trades.append({
                        'buy_time': buy_order['time'],
                        'sell_time': sell_order['time'],
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'quantity': quantity,
                        'pnl': pnl,
                        'buy_order_id': buy_order['orderId'],
                        'sell_order_id': sell_order['orderId']
                    })
            
            # Статистика
            total_trades = len(trades)
            profitable_trades = len([t for t in trades if t['pnl'] > 0])
            total_pnl = sum(t['pnl'] for t in trades)
            max_profit = max([t['pnl'] for t in trades]) if trades else 0.0
            max_loss = min([t['pnl'] for t in trades]) if trades else 0.0
            avg_profit = total_pnl / total_trades if total_trades > 0 else 0.0
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            return {
                'symbol': symbol,
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'total_pnl': total_pnl,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'avg_profit': avg_profit,
                'win_rate': win_rate,
                'trades': trades
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return {
                'symbol': symbol,
                'total_trades': 0,
                'profitable_trades': 0,
                'total_pnl': 0.0,
                'max_profit': 0.0,
                'max_loss': 0.0,
                'avg_profit': 0.0,
                'win_rate': 0.0,
                'trades': []
            }
    
    def format_scalpers_report(self) -> str:
        """Форматировать отчет по скальперам"""
        try:
            # Анализируем оба скальпера
            btc_analysis = self.analyze_scalper_performance('BTCUSDC')
            eth_analysis = self.analyze_scalper_performance('ETHUSDC')
            
            # Получаем данные от менеджера скальперов
            btc_manager_data = self.get_manager_scalpers_data('BTCUSDC')
            eth_manager_data = self.get_manager_scalpers_data('ETHUSDC')
            
            # Общая статистика
            total_trades = btc_analysis['total_trades'] + eth_analysis['total_trades']
            total_pnl = btc_analysis['total_pnl'] + eth_analysis['total_pnl']
            total_profitable = btc_analysis['profitable_trades'] + eth_analysis['profitable_trades']
            overall_win_rate = (total_profitable / total_trades * 100) if total_trades > 0 else 0.0
            
            message = "<b>⚡ ОТЧЕТ СКАЛЬПЕРОВ (≤$5)</b>\n"
            message += "<i>📅 Учитываются сделки с 11:25 по Москве</i>\n"
            message += "=" * 50 + "\n\n"
            
            # Добавляем информацию о менеджере скальперов
            if btc_manager_data or eth_manager_data:
                message += "<b>🎯 МЕНЕДЖЕР СКАЛЬПЕРОВ</b>\n"
                if btc_manager_data:
                    message += f"🔴 BTC: {btc_manager_data.get('active_scalpers', 0)} активных, {btc_manager_data.get('stuck_scalpers', 0)} застрявших\n"
                if eth_manager_data:
                    message += f"🔵 ETH: {eth_manager_data.get('active_scalpers', 0)} активных, {eth_manager_data.get('stuck_scalpers', 0)} застрявших\n"
                message += "\n"
            
            # BTC Скальпер
            message += "<b>🔴 BTC СКАЛЬПЕР (BTCUSDC)</b>\n"
            message += f"📊 Всего сделок: {btc_analysis['total_trades']}\n"
            message += f"✅ Прибыльных: {btc_analysis['profitable_trades']}\n"
            message += f"📈 Винрейт: {btc_analysis['win_rate']:.1f}%\n"
            message += f"💰 Общий PnL: ${btc_analysis['total_pnl']:.4f} USDC\n"
            message += f"📈 Макс. прибыль: ${btc_analysis['max_profit']:.4f} USDC\n"
            message += f"📉 Макс. убыток: ${btc_analysis['max_loss']:.4f} USDC\n"
            message += f"📊 Средняя прибыль: ${btc_analysis['avg_profit']:.4f} USDC\n\n"
            
            # ETH Скальпер
            message += "<b>🔵 ETH СКАЛЬПЕР (ETHUSDC)</b>\n"
            message += f"📊 Всего сделок: {eth_analysis['total_trades']}\n"
            message += f"✅ Прибыльных: {eth_analysis['profitable_trades']}\n"
            message += f"📈 Винрейт: {eth_analysis['win_rate']:.1f}%\n"
            message += f"💰 Общий PnL: ${eth_analysis['total_pnl']:.4f} USDC\n"
            message += f"📈 Макс. прибыль: ${eth_analysis['max_profit']:.4f} USDC\n"
            message += f"📉 Макс. убыток: ${eth_analysis['max_loss']:.4f} USDC\n"
            message += f"📊 Средняя прибыль: ${eth_analysis['avg_profit']:.4f} USDC\n\n"
            
            # Общая статистика
            message += "<b>📊 ОБЩАЯ СТАТИСТИКА</b>\n"
            message += f"📈 Всего сделок: {total_trades}\n"
            message += f"✅ Прибыльных: {total_profitable}\n"
            message += f"📈 Общий винрейт: {overall_win_rate:.1f}%\n"
            message += f"💰 Общий PnL: ${total_pnl:.4f} USDC\n\n"
            
            # Последние сделки
            message += "<b>🕐 ПОСЛЕДНИЕ СДЕЛКИ</b>\n"
            
            # BTC последние сделки
            if btc_analysis['trades']:
                message += "<b>🔴 BTC:</b>\n"
                for trade in btc_analysis['trades'][-3:]:  # Последние 3
                    buy_time = datetime.fromtimestamp(trade['buy_time'] / 1000).strftime('%H:%M')
                    sell_time = datetime.fromtimestamp(trade['sell_time'] / 1000).strftime('%H:%M')
                    pnl_status = "📈" if trade['pnl'] > 0 else "📉"
                    message += f"{pnl_status} {buy_time}→{sell_time}: ${trade['buy_price']:.2f}→${trade['sell_price']:.2f} | ${trade['pnl']:.4f}\n"
            
            # ETH последние сделки
            if eth_analysis['trades']:
                message += "<b>🔵 ETH:</b>\n"
                for trade in eth_analysis['trades'][-3:]:  # Последние 3
                    buy_time = datetime.fromtimestamp(trade['buy_time'] / 1000).strftime('%H:%M')
                    sell_time = datetime.fromtimestamp(trade['sell_time'] / 1000).strftime('%H:%M')
                    pnl_status = "📈" if trade['pnl'] > 0 else "📉"
                    message += f"{pnl_status} {buy_time}→{sell_time}: ${trade['buy_price']:.2f}→${trade['sell_price']:.2f} | ${trade['pnl']:.4f}\n"
            
            # Добавляем последние сделки менеджера
            if btc_manager_data.get('scalpers') or eth_manager_data.get('scalpers'):
                message += "\n<b>🎯 ПОСЛЕДНИЕ СДЕЛКИ МЕНЕДЖЕРА</b>\n"
                
                # BTC скальперы менеджера
                if btc_manager_data.get('scalpers'):
                    message += "<b>🔴 BTC менеджер:</b>\n"
                    for scalper in btc_manager_data['scalpers'][-3:]:  # Последние 3
                        status_emoji = "✅" if scalper.status.value == 'active' else "⚠️" if scalper.status.value == 'stuck' else "💰"
                        message += f"{status_emoji} {scalper.id}: ${scalper.entry_price:.2f} | {scalper.status.value}\n"
                
                # ETH скальперы менеджера
                if eth_manager_data.get('scalpers'):
                    message += "<b>🔵 ETH менеджер:</b>\n"
                    for scalper in eth_manager_data['scalpers'][-3:]:  # Последние 3
                        status_emoji = "✅" if scalper.status.value == 'active' else "⚠️" if scalper.status.value == 'stuck' else "💰"
                        message += f"{status_emoji} {scalper.id}: ${scalper.entry_price:.2f} | {scalper.status.value}\n"
            
            message += f"\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка форматирования отчета: {e}")
            return f"❌ Ошибка отчета скальперов: {e}"
    
    def send_report(self):
        """Отправить отчет"""
        try:
            report = self.format_scalpers_report()
            self.send_telegram_message(report)
            logger.info("📊 Отчет скальперов отправлен")
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
    
    def start(self):
        """Запустить репортер"""
        logger.info("🚀 Запуск репортера скальперов...")
        logger.info(f"⏰ Интервал отчетов: {self.report_interval_sec} сек")
        
        # Отправляем первый отчет
        self.send_report()
        
        self.is_running = True
        
        while self.is_running:
            try:
                time.sleep(self.report_interval_sec)
                if self.is_running:
                    self.send_report()
            except KeyboardInterrupt:
                logger.info("🛑 Репортер скальперов остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле репортера: {e}")
                time.sleep(60)
    
    def stop(self):
        """Остановить репортер"""
        logger.info("🛑 Остановка репортера скальперов")
        self.is_running = False

# Функция для запуска в отдельном потоке
def run_scalpers_reporter():
    """Запустить репортер скальперов в отдельном потоке"""
    reporter = ScalpersReporter()
    reporter.start()

if __name__ == "__main__":
    # Тестовый запуск
    reporter = ScalpersReporter()
    reporter.send_report()
