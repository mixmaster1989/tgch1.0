#!/usr/bin/env python3
"""
Расчет реального PnL на основе истории ордеров
Анализирует покупки и продажи для точного расчета прибыли/убытка
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealPnLCalculator:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Минимальная прибыль для отображения (в USD)
        self.min_profit_usd = 0.01  # $0.01 - даже маленькая прибыль
        
        # Период анализа (последние 30 дней)
        self.analysis_days = 30
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.info(f"Telegram: {message}")
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
    
    def get_order_history_for_symbol(self, symbol: str) -> List[Dict]:
        """Получить историю ордеров для символа"""
        try:
            # Получаем историю ордеров за последние 30 дней
            end_time = int(time.time() * 1000)
            start_time = end_time - (self.analysis_days * 24 * 60 * 60 * 1000)
            
            orders = self.mex_api.get_order_history(symbol=symbol, limit=1000)
            
            if not isinstance(orders, list):
                logger.warning(f"Неверный формат истории ордеров для {symbol}")
                return []
            
            # Фильтруем только исполненные ордера за нужный период
            filtered_orders = []
            for order in orders:
                if order.get('status') == 'FILLED':
                    order_time = int(order.get('time', 0))
                    if start_time <= order_time <= end_time:
                        filtered_orders.append(order)
            
            logger.info(f"📊 Найдено {len(filtered_orders)} исполненных ордеров для {symbol}")
            return filtered_orders
            
        except Exception as e:
            logger.error(f"Ошибка получения истории ордеров для {symbol}: {e}")
            return []
    
    def calculate_symbol_pnl(self, symbol: str, current_balance: float) -> Optional[Dict]:
        """Рассчитать PnL для конкретного символа"""
        try:
            # Получаем историю ордеров
            orders = self.get_order_history_for_symbol(symbol)
            if not orders:
                return None
            
            # Разделяем на покупки и продажи
            buys = []
            sells = []
            
            for order in orders:
                side = order.get('side', '').upper()
                price = float(order.get('price', 0))
                quantity = float(order.get('executedQty', 0))
                time_ms = int(order.get('time', 0))
                
                if side == 'BUY' and quantity > 0:
                    buys.append({
                        'price': price,
                        'quantity': quantity,
                        'time': time_ms,
                        'value': price * quantity
                    })
                elif side == 'SELL' and quantity > 0:
                    sells.append({
                        'price': price,
                        'quantity': quantity,
                        'time': time_ms,
                        'value': price * quantity
                    })
            
            # Рассчитываем среднюю цену покупки
            total_buy_quantity = sum(buy['quantity'] for buy in buys)
            total_buy_value = sum(buy['value'] for buy in buys)
            
            if total_buy_quantity == 0:
                return None
            
            avg_buy_price = total_buy_value / total_buy_quantity
            
            # Получаем текущую цену
            current_price = self.get_current_price(symbol)
            if not current_price:
                return None
            
            # Рассчитываем PnL
            current_value = current_balance * current_price
            total_invested = current_balance * avg_buy_price
            
            pnl_usd = current_value - total_invested
            pnl_percent = (pnl_usd / total_invested * 100) if total_invested > 0 else 0
            
            return {
                'symbol': symbol,
                'current_balance': current_balance,
                'current_price': current_price,
                'avg_buy_price': avg_buy_price,
                'current_value': current_value,
                'total_invested': total_invested,
                'pnl_usd': pnl_usd,
                'pnl_percent': pnl_percent,
                'is_profitable': pnl_usd >= self.min_profit_usd,
                'buy_orders': len(buys),
                'sell_orders': len(sells)
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета PnL для {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Получить текущую цену символа"""
        try:
            ticker = self.mex_api.get_ticker_price(symbol)
            if 'price' in ticker:
                return float(ticker['price'])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены для {symbol}: {e}")
            return None
    
    def get_account_balances(self) -> Dict:
        """Получить балансы аккаунта"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                logger.error("Не удалось получить балансы")
                return {}
            
            balances = {}
            for balance in account_info['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:  # Только ненулевые балансы
                    balances[asset] = total
            
            return balances
            
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return {}
    
    def find_profitable_positions(self) -> List[Dict]:
        """Найти позиции в плюсе на основе реального PnL"""
        try:
            logger.info("🔍 Поиск позиций в плюсе (реальный PnL)...")
            
            # Получаем балансы
            balances = self.get_account_balances()
            if not balances:
                logger.error("Не удалось получить балансы")
                return []
            
            logger.info(f"📊 Найдено {len(balances)} активов с балансом")
            
            # Исключаем стейблкоины
            excluded_assets = {'USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FRAX'}
            
            profitable_positions = []
            total_profit_usd = 0.0
            
            for asset, balance in balances.items():
                if asset in excluded_assets:
                    continue
                
                if balance < 0.0001:  # Пропускаем очень мелкие балансы
                    continue
                
                # Формируем торговую пару
                if asset == 'BTC':
                    symbol = 'BTCUSDT'
                elif asset == 'ETH':
                    symbol = 'ETHUSDC'
                else:
                    symbol = f'{asset}USDT'
                
                # Рассчитываем PnL
                pnl_data = self.calculate_symbol_pnl(symbol, balance)
                
                if pnl_data and pnl_data['is_profitable']:
                    profitable_positions.append(pnl_data)
                    total_profit_usd += pnl_data['pnl_usd']
            
            # Сортируем по прибыли
            profitable_positions.sort(key=lambda x: x['pnl_usd'], reverse=True)
            
            logger.info(f"✅ Найдено {len(profitable_positions)} позиций в плюсе")
            logger.info(f"💰 Общая прибыль: ${total_profit_usd:.2f}")
            
            return profitable_positions
            
        except Exception as e:
            logger.error(f"Ошибка поиска позиций: {e}")
            return []
    
    def format_profitable_positions_report(self, positions: List[Dict]) -> str:
        """Форматировать отчет о прибыльных позициях"""
        if not positions:
            return "📊 <b>Прибыльные позиции не найдены</b>\n\n💡 Попробуйте увеличить период анализа или минимальную прибыль"
        
        total_profit = sum(pos['pnl_usd'] for pos in positions)
        total_value = sum(pos['current_value'] for pos in positions)
        total_invested = sum(pos['total_invested'] for pos in positions)
        
        report = f"📈 <b>ПРИБЫЛЬНЫЕ ПОЗИЦИИ (РЕАЛЬНЫЙ PnL)</b>\n\n"
        report += f"💰 Общая прибыль: <b>${total_profit:.2f}</b>\n"
        report += f"📊 Общая стоимость: <b>${total_value:.2f}</b>\n"
        report += f"💼 Вложено: <b>${total_invested:.2f}</b>\n"
        report += f"📈 Количество позиций: <b>{len(positions)}</b>\n\n"
        
        report += "🔍 <b>Детализация:</b>\n"
        report += "─" * 50 + "\n"
        
        for i, pos in enumerate(positions[:10], 1):  # Показываем топ-10
            report += f"{i}. <b>{pos['symbol']}</b>\n"
            report += f"   💰 Текущая стоимость: ${pos['current_value']:.2f}\n"
            report += f"   📈 Прибыль: ${pos['pnl_usd']:.2f} ({pos['pnl_percent']:.1f}%)\n"
            report += f"   💵 Средняя цена покупки: ${pos['avg_buy_price']:.4f}\n"
            report += f"   📊 Текущая цена: ${pos['current_price']:.4f}\n"
            report += f"   🔢 Баланс: {pos['current_balance']:.6f}\n"
            report += f"   📋 Ордера: {pos['buy_orders']} покупок, {pos['sell_orders']} продаж\n\n"
        
        if len(positions) > 10:
            report += f"... и еще {len(positions) - 10} позиций\n\n"
        
        report += f"⏰ Период анализа: {self.analysis_days} дней\n"
        report += f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
        
        return report
    
    def run_analysis(self):
        """Запустить анализ прибыльных позиций"""
        try:
            logger.info("🚀 Запуск анализа реального PnL...")
            
            # Находим прибыльные позиции
            positions = self.find_profitable_positions()
            
            # Формируем отчет
            report = self.format_profitable_positions_report(positions)
            
            # Отправляем в Telegram
            self.send_telegram_message(report)
            
            # Выводим в консоль
            print("\n" + "="*60)
            print("📊 ОТЧЕТ О ПРИБЫЛЬНЫХ ПОЗИЦИЯХ (РЕАЛЬНЫЙ PnL)")
            print("="*60)
            print(report.replace('<b>', '').replace('</b>', ''))
            print("="*60)
            
            return positions
            
        except Exception as e:
            error_msg = f"❌ Ошибка анализа: {e}"
            logger.error(error_msg)
            self.send_telegram_message(error_msg)
            return []

def main():
    """Основная функция"""
    calculator = RealPnLCalculator()
    calculator.run_analysis()

if __name__ == "__main__":
    main()







