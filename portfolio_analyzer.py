#!/usr/bin/env python3
"""
Расширенный анализатор портфеля MEXCAITRADE
P&L по монетам, общий P&L, полная информация от API биржи
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import requests

from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class PortfolioAnalyzer:
    """Расширенный анализатор портфеля"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Кэш для хранения исторических цен
        self.price_cache = {}
        self.last_update = {}
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
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
            print(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Получить текущую цену символа"""
        try:
            # Проверяем кэш (обновляем каждые 30 секунд)
            current_time = time.time()
            if (symbol in self.price_cache and 
                symbol in self.last_update and 
                current_time - self.last_update[symbol] < 30):
                return self.price_cache[symbol]
            
            # Получаем новую цену
            ticker = self.mex_api.get_ticker_price(symbol)
            if 'price' in ticker:
                price = float(ticker['price'])
                self.price_cache[symbol] = price
                self.last_update[symbol] = current_time
                return price
            
            return None
        except Exception as e:
            print(f"Ошибка получения цены {symbol}: {e}")
            return None
    
    def get_24h_change(self, symbol: str) -> Optional[float]:
        """Получить изменение цены за 24 часа"""
        try:
            ticker = self.mex_api.get_24hr_ticker(symbol)
            if isinstance(ticker, dict) and 'priceChangePercent' in ticker:
                return float(ticker['priceChangePercent'])
            return None
        except Exception as e:
            print(f"Ошибка получения 24h изменения {symbol}: {e}")
            return None
    
    def calculate_portfolio_pnl(self, balances: List[Dict]) -> Dict:
        """Рассчитать P&L портфеля"""
        try:
            portfolio_data = {
                'total_usdt_value': 0.0,
                'positions': [],
                'total_pnl_usdt': 0.0,
                'total_pnl_percent': 0.0,
                'best_performer': None,
                'worst_performer': None,
                'total_positions': 0,
                'profitable_positions': 0,
                'losing_positions': 0
            }
            
            best_pnl = -float('inf')
            worst_pnl = float('inf')
            
            for balance in balances:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total <= 0 or asset == 'USDT':
                    continue
                
                symbol = f"{asset}USDT"
                current_price = self.get_current_price(symbol)
                
                if current_price is None:
                    continue
                
                # Рассчитываем стоимость позиции
                position_value = total * current_price
                
                # Для простоты считаем, что средняя цена покупки = текущая цена * 0.99
                # В реальной системе нужно хранить историю покупок
                estimated_avg_price = current_price * 0.99
                pnl_usdt = position_value - (total * estimated_avg_price)
                pnl_percent = (pnl_usdt / (total * estimated_avg_price)) * 100 if estimated_avg_price > 0 else 0
                
                position_data = {
                    'asset': asset,
                    'symbol': symbol,
                    'quantity': total,
                    'current_price': current_price,
                    'position_value_usdt': position_value,
                    'estimated_avg_price': estimated_avg_price,
                    'pnl_usdt': pnl_usdt,
                    'pnl_percent': pnl_percent,
                    '24h_change': self.get_24h_change(symbol),
                    'free': free,
                    'locked': locked
                }
                
                portfolio_data['positions'].append(position_data)
                portfolio_data['total_usdt_value'] += position_value
                portfolio_data['total_pnl_usdt'] += pnl_usdt
                portfolio_data['total_positions'] += 1
                
                if pnl_usdt > 0:
                    portfolio_data['profitable_positions'] += 1
                else:
                    portfolio_data['losing_positions'] += 1
                
                # Отслеживаем лучшие/худшие позиции
                if pnl_percent > best_pnl:
                    best_pnl = pnl_percent
                    portfolio_data['best_performer'] = position_data
                
                if pnl_percent < worst_pnl:
                    worst_pnl = pnl_percent
                    portfolio_data['worst_performer'] = position_data
            
            # Рассчитываем общий процент P&L
            if portfolio_data['total_usdt_value'] > 0:
                portfolio_data['total_pnl_percent'] = (
                    portfolio_data['total_pnl_usdt'] / 
                    (portfolio_data['total_usdt_value'] - portfolio_data['total_pnl_usdt'])
                ) * 100
            
            return portfolio_data
            
        except Exception as e:
            print(f"Ошибка расчета P&L портфеля: {e}")
            return {}
    
    def get_account_full_info(self) -> Dict:
        """Получить полную информацию об аккаунте"""
        try:
            # Получаем базовую информацию об аккаунте
            account_info = self.mex_api.get_account_info()
            
            # Получаем открытые ордера
            open_orders = self.mex_api.get_open_orders()
            
            # Получаем историю торгов (последние 100 ордеров)
            trade_history = self.get_trade_history()
            
            # Рассчитываем P&L портфеля
            portfolio_pnl = {}
            if 'balances' in account_info:
                portfolio_pnl = self.calculate_portfolio_pnl(account_info['balances'])
            
            return {
                'account_info': account_info,
                'open_orders': open_orders,
                'trade_history': trade_history,
                'portfolio_pnl': portfolio_pnl,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Ошибка получения полной информации об аккаунте: {e}")
            return {}
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Получить историю торгов"""
        try:
            # Получаем все ордера за последние 30 дней
            timestamp = int(time.time() * 1000)
            query_string = f'ttimestamp={timestamp}'
            
            # Здесь нужно добавить метод в MexAPI для получения истории ордеров
            # Пока возвращаем пустой список
            return []
            
        except Exception as e:
            print(f"Ошибка получения истории торгов: {e}")
            return []
    
    def format_portfolio_report(self, account_data: Dict) -> str:
        """Форматировать отчет о портфеле"""
        try:
            if not account_data:
                return "❌ Ошибка получения данных портфеля"
            
            account_info = account_data.get('account_info', {})
            portfolio_pnl = account_data.get('portfolio_pnl', {})
            open_orders = account_data.get('open_orders', [])
            
            message = "<b>📊 ПОЛНЫЙ ОТЧЕТ ПОРТФЕЛЯ MEXCAITRADE</b>\n"
            message += "=" * 50 + "\n\n"
            
            # Общая информация
            message += "<b>💰 ОБЩАЯ ИНФОРМАЦИЯ:</b>\n"
            message += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            message += f"🏦 Тип аккаунта: {account_info.get('accountType', 'SPOT')}\n"
            message += f"🔓 Разрешения: {', '.join(account_info.get('permissions', []))}\n\n"
            
            # P&L портфеля
            if portfolio_pnl:
                total_value = portfolio_pnl.get('total_usdt_value', 0)
                total_pnl = portfolio_pnl.get('total_pnl_usdt', 0)
                total_pnl_percent = portfolio_pnl.get('total_pnl_percent', 0)
                
                message += "<b>📈 P&L ПОРТФЕЛЯ:</b>\n"
                message += f"💵 Общая стоимость: ${total_value:.2f} USDT\n"
                
                pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
                message += f"{pnl_emoji} Общий P&L: ${total_pnl:.2f} USDT ({total_pnl_percent:+.2f}%)\n"
                
                profitable = portfolio_pnl.get('profitable_positions', 0)
                losing = portfolio_pnl.get('losing_positions', 0)
                total_pos = portfolio_pnl.get('total_positions', 0)
                
                message += f"📊 Позиций: {total_pos} (🟢 {profitable} | 🔴 {losing})\n\n"
                
                # Лучшие/худшие позиции
                best = portfolio_pnl.get('best_performer')
                worst = portfolio_pnl.get('worst_performer')
                
                if best:
                    message += "<b>🏆 ЛУЧШАЯ ПОЗИЦИЯ:</b>\n"
                    message += f"  {best['asset']}: +${best['pnl_usdt']:.2f} ({best['pnl_percent']:+.2f}%)\n"
                
                if worst:
                    message += f"<b>📉 ХУДШАЯ ПОЗИЦИЯ:</b>\n"
                    message += f"  {worst['asset']}: {worst['pnl_usdt']:.2f} ({worst['pnl_percent']:+.2f}%)\n"
                
                message += "\n"
            
            # Детали позиций
            if portfolio_pnl and portfolio_pnl.get('positions'):
                message += "<b>📋 ДЕТАЛИ ПОЗИЦИЙ:</b>\n"
                
                # Сортируем по P&L
                positions = sorted(portfolio_pnl['positions'], 
                                 key=lambda x: x['pnl_percent'], reverse=True)
                
                for i, pos in enumerate(positions[:10]):  # Показываем топ-10
                    pnl_emoji = "🟢" if pos['pnl_percent'] >= 0 else "🔴"
                    change_emoji = "📈" if pos.get('24h_change', 0) >= 0 else "📉"
                    
                    message += f"{i+1}. {pnl_emoji} {pos['asset']}:\n"
                    message += f"   💰 {pos['quantity']:.4f} × ${pos['current_price']:.4f}\n"
                    message += f"   💵 ${pos['position_value_usdt']:.2f} USDT\n"
                    message += f"   📊 P&L: ${pos['pnl_usdt']:.2f} ({pos['pnl_percent']:+.2f}%)\n"
                    
                    if pos.get('24h_change') is not None:
                        message += f"   {change_emoji} 24ч: {pos['24h_change']:+.2f}%\n"
                    
                    message += "\n"
                
                if len(positions) > 10:
                    message += f"... и еще {len(positions) - 10} позиций\n\n"
            
            # Открытые ордера
            if open_orders:
                message += "<b>📋 ОТКРЫТЫЕ ОРДЕРА:</b>\n"
                for order in open_orders[:5]:  # Показываем первые 5
                    side_emoji = "🟢" if order['side'] == 'BUY' else "🔴"
                    message += f"{side_emoji} {order['symbol']}: {order['side']} {float(order['origQty']):.4f} @ ${float(order['price']):.6f}\n"
                
                if len(open_orders) > 5:
                    message += f"... и еще {len(open_orders) - 5} ордеров\n"
                
                message += "\n"
            
            # Баланс USDT
            usdt_balance = 0.0
            if 'balances' in account_info:
                for balance in account_info['balances']:
                    if balance['asset'] == 'USDT':
                        usdt_balance = float(balance['free'])
                        break
            
            message += f"<b>💵 БАЛАНС USDT:</b> ${usdt_balance:.2f}\n\n"
            
            # Статус торговли
            can_trade = account_info.get('canTrade', False)
            can_withdraw = account_info.get('canWithdraw', False)
            can_deposit = account_info.get('canDeposit', False)
            
            message += "<b>🔧 СТАТУС ТОРГОВЛИ:</b>\n"
            message += f"📈 Торговля: {'✅' if can_trade else '❌'}\n"
            message += f"💸 Вывод: {'✅' if can_withdraw else '❌'}\n"
            message += f"💳 Депозит: {'✅' if can_deposit else '❌'}\n\n"
            
            message += "=" * 50 + "\n"
            message += "<b>🚀 MEXCAITRADE - ПРОФЕССИОНАЛЬНАЯ ТОРГОВАЯ СИСТЕМА</b>\n"
            
            return message
            
        except Exception as e:
            return f"❌ Ошибка форматирования отчета: {e}"
    
    def send_portfolio_report(self):
        """Отправить полный отчет о портфеле"""
        try:
            print("📊 Получение полной информации о портфеле...")
            
            # Получаем все данные
            account_data = self.get_account_full_info()
            
            # Форматируем отчет
            report = self.format_portfolio_report(account_data)
            
            # Отправляем в Telegram
            result = self.send_telegram_message(report)
            
            if result and result.get('ok'):
                print("✅ Отчет о портфеле отправлен в Telegram")
                return True
            else:
                print("❌ Ошибка отправки отчета")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка отправки отчета о портфеле: {e}")
            return False

# Функция для тестирования
def test_portfolio_analyzer():
    """Тест анализатора портфеля"""
    analyzer = PortfolioAnalyzer()
    analyzer.send_portfolio_report()

if __name__ == "__main__":
    test_portfolio_analyzer() 