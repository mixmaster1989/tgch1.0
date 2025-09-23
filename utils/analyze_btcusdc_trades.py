#!/usr/bin/env python3
"""
Анализ последних сделок по BTCUSDC
Получаем PnL, комиссии и детали сделок через MEX API
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from mex_api import MexAPI

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BTCTradeAnalyzer:
    """Анализатор сделок по BTCUSDC"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.symbol = 'BTCUSDC'
        
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Получить последние сделки по BTCUSDC"""
        try:
            logger.info(f"🔍 Получаем последние {limit} сделок по {self.symbol}...")
            
            # Получаем историю ордеров
            orders = self.mex_api.get_order_history(symbol=self.symbol, limit=limit)
            
            if not orders or 'code' in orders:
                logger.error(f"❌ Ошибка получения истории ордеров: {orders}")
                return []
            
            # Фильтруем только исполненные ордера
            executed_orders = [
                order for order in orders 
                if order.get('status') == 'FILLED'
            ]
            
            logger.info(f"✅ Получено {len(executed_orders)} исполненных ордеров")
            return executed_orders
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения сделок: {e}")
            return []
    
    def get_current_price(self) -> Optional[float]:
        """Получить текущую цену BTCUSDC"""
        try:
            ticker = self.mex_api.get_ticker_price(self.symbol)
            if ticker and 'price' in ticker:
                return float(ticker['price'])
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения цены: {e}")
            return None
    
    def calculate_pnl(self, order: Dict, current_price: float) -> Dict:
        """Рассчитать PnL для ордера"""
        try:
            side = order.get('side', 'BUY')
            executed_qty = float(order.get('executedQty', 0))
            price = float(order.get('price', 0))
            commission = float(order.get('commission', 0))
            commission_asset = order.get('commissionAsset', 'USDC')
            
            if side == 'BUY':
                # Покупка - рассчитываем потенциальную прибыль при продаже по текущей цене
                cost_basis = executed_qty * price
                current_value = executed_qty * current_price
                unrealized_pnl = current_value - cost_basis
                pnl_percent = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                
                return {
                    'type': 'BUY',
                    'quantity': executed_qty,
                    'entry_price': price,
                    'current_price': current_price,
                    'cost_basis': cost_basis,
                    'current_value': current_value,
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_percent': pnl_percent,
                    'commission': commission,
                    'commission_asset': commission_asset,
                    'total_cost': cost_basis + commission
                }
            else:
                # Продажа - рассчитываем реализованную прибыль
                revenue = executed_qty * price
                # Для продажи нужна информация о покупке, но у нас нет полной истории
                return {
                    'type': 'SELL',
                    'quantity': executed_qty,
                    'sell_price': price,
                    'revenue': revenue,
                    'commission': commission,
                    'commission_asset': commission_asset,
                    'net_revenue': revenue - commission
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка расчета PnL: {e}")
            return {}
    
    def analyze_trades(self, trades: List[Dict]) -> Dict:
        """Анализ всех сделок"""
        try:
            if not trades:
                return {}
            
            current_price = self.get_current_price()
            if not current_price:
                logger.error("❌ Не удалось получить текущую цену")
                return {}
            
            logger.info(f"💰 Текущая цена {self.symbol}: ${current_price:.2f}")
            
            total_buy_qty = 0.0
            total_buy_cost = 0.0
            total_commission = 0.0
            total_sell_qty = 0.0
            total_sell_revenue = 0.0
            
            buy_orders = []
            sell_orders = []
            
            for trade in trades:
                side = trade.get('side', 'BUY')
                executed_qty = float(trade.get('executedQty', 0))
                price = float(trade.get('price', 0))
                commission = float(trade.get('commission', 0))
                commission_asset = trade.get('commissionAsset', 'USDC')
                
                if side == 'BUY':
                    total_buy_qty += executed_qty
                    total_buy_cost += executed_qty * price
                    total_commission += commission
                    buy_orders.append(trade)
                else:
                    total_sell_qty += executed_qty
                    total_sell_revenue += executed_qty * price
                    total_commission += commission
                    sell_orders.append(trade)
            
            # Рассчитываем общий PnL
            total_commission_usdc = total_commission  # Предполагаем, что комиссии в USDC
            
            if total_buy_qty > 0:
                avg_buy_price = total_buy_cost / total_buy_qty
                current_value = total_buy_qty * current_price
                unrealized_pnl = current_value - total_buy_cost
                unrealized_pnl_percent = (unrealized_pnl / total_buy_cost) * 100 if total_buy_cost > 0 else 0
                
                # PnL с учетом комиссий
                total_pnl = unrealized_pnl - total_commission_usdc
                total_pnl_percent = (total_pnl / total_buy_cost) * 100 if total_buy_cost > 0 else 0
            else:
                avg_buy_price = 0.0
                current_value = 0.0
                unrealized_pnl = 0.0
                unrealized_pnl_percent = 0.0
                total_pnl = 0.0
                total_pnl_percent = 0.0
            
            return {
                'summary': {
                    'total_buy_quantity': total_buy_qty,
                    'total_buy_cost': total_buy_cost,
                    'total_sell_quantity': total_sell_qty,
                    'total_sell_revenue': total_sell_revenue,
                    'total_commission': total_commission_usdc,
                    'avg_buy_price': avg_buy_price,
                    'current_price': current_price,
                    'current_value': current_value,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_percent': unrealized_pnl_percent,
                    'total_pnl': total_pnl,
                    'total_pnl_percent': total_pnl_percent
                },
                'buy_orders': buy_orders,
                'sell_orders': sell_orders,
                'all_trades': trades
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа сделок: {e}")
            return {}
    
    def format_trade_report(self, analysis: Dict) -> str:
        """Форматировать отчет о сделках"""
        try:
            if not analysis:
                return "❌ Нет данных для анализа"
            
            summary = analysis['summary']
            buy_orders = analysis['buy_orders']
            sell_orders = analysis['sell_orders']
            
            message = f"<b>📊 АНАЛИЗ СДЕЛОК {self.symbol}</b>\n"
            message += "=" * 50 + "\n\n"
            
            message += f"📅 Время анализа: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            message += f"💰 Текущая цена: ${summary['current_price']:.2f}\n\n"
            
            message += "<b>📈 ПОКУПКИ:</b>\n"
            message += f"   Количество: {summary['total_buy_quantity']:.6f} BTC\n"
            message += f"   Общая стоимость: ${summary['total_buy_cost']:.2f} USDC\n"
            message += f"   Средняя цена: ${summary['avg_buy_price']:.2f} USDC\n\n"
            
            message += "<b>📉 ПРОДАЖИ:</b>\n"
            message += f"   Количество: {summary['total_sell_quantity']:.6f} BTC\n"
            message += f"   Общая выручка: ${summary['total_sell_revenue']:.2f} USDC\n\n"
            
            message += "<b>💸 КОМИССИИ:</b>\n"
            message += f"   Общая комиссия: ${summary['total_commission']:.4f} USDC\n"
            message += f"   Комиссия в % от покупок: {(summary['total_commission']/summary['total_buy_cost']*100):.2f}%\n\n"
            
            message += "<b>📊 P&L АНАЛИЗ:</b>\n"
            message += f"   Текущая стоимость: ${summary['current_value']:.2f} USDC\n"
            message += f"   Нереализованный P&L: ${summary['unrealized_pnl']:.2f} USDC ({summary['unrealized_pnl_percent']:.2f}%)\n"
            message += f"   Общий P&L (с комиссиями): ${summary['total_pnl']:.2f} USDC ({summary['total_pnl_percent']:.2f}%)\n\n"
            
            message += "<b>🔍 ПОСЛЕДНИЕ СДЕЛКИ:</b>\n"
            
            # Показываем последние 5 сделок
            recent_trades = analysis['all_trades'][:5]
            for i, trade in enumerate(recent_trades, 1):
                side = trade.get('side', 'BUY')
                qty = float(trade.get('executedQty', 0))
                price = float(trade.get('price', 0))
                commission = float(trade.get('commission', 0))
                time_str = datetime.fromtimestamp(int(trade.get('time', 0))/1000).strftime('%H:%M:%S')
                
                emoji = "🟢" if side == 'BUY' else "🔴"
                message += f"   {i}. {emoji} {side} {qty:.6f} BTC @ ${price:.2f} | Комиссия: ${commission:.4f} | {time_str}\n"
            
            message += "\n" + "=" * 50 + "\n"
            message += "<b>📊 АНАЛИЗ СДЕЛОК BTCUSDC</b>"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования отчета: {e}")
            return f"❌ Ошибка отчета: {e}"
    
    def run_analysis(self, limit: int = 50) -> None:
        """Запустить полный анализ"""
        try:
            print(f"🚀 АНАЛИЗ СДЕЛОК ПО {self.symbol}")
            print("=" * 60)
            
            # Получаем сделки
            trades = self.get_recent_trades(limit)
            if not trades:
                print("❌ Не удалось получить данные о сделках")
                return
            
            # Анализируем
            analysis = self.analyze_trades(trades)
            if not analysis:
                print("❌ Не удалось проанализировать сделки")
                return
            
            # Выводим результаты
            summary = analysis['summary']
            
            print(f"📊 ОБЩАЯ СТАТИСТИКА:")
            print(f"   Покупки: {summary['total_buy_quantity']:.6f} BTC на ${summary['total_buy_cost']:.2f} USDC")
            print(f"   Продажи: {summary['total_sell_quantity']:.6f} BTC на ${summary['total_sell_revenue']:.2f} USDC")
            print(f"   Комиссии: ${summary['total_commission']:.4f} USDC")
            print(f"   Средняя цена покупки: ${summary['avg_buy_price']:.2f} USDC")
            print(f"   Текущая цена: ${summary['current_price']:.2f} USDC")
            print()
            
            print(f"💰 P&L АНАЛИЗ:")
            print(f"   Нереализованный P&L: ${summary['unrealized_pnl']:.2f} USDC ({summary['unrealized_pnl_percent']:.2f}%)")
            print(f"   Общий P&L (с комиссиями): ${summary['total_pnl']:.2f} USDC ({summary['total_pnl_percent']:.2f}%)")
            print()
            
            print(f"🔍 ПОСЛЕДНИЕ СДЕЛКИ:")
            recent_trades = analysis['all_trades'][:10]
            for i, trade in enumerate(recent_trades, 1):
                side = trade.get('side', 'BUY')
                qty = float(trade.get('executedQty', 0))
                price = float(trade.get('price', 0))
                commission = float(trade.get('commission', 0))
                time_str = datetime.fromtimestamp(int(trade.get('time', 0))/1000).strftime('%d.%m %H:%M:%S')
                
                emoji = "🟢" if side == 'BUY' else "🔴"
                print(f"   {i:2d}. {emoji} {side:4s} {qty:8.6f} BTC @ ${price:8.2f} | Комиссия: ${commission:6.4f} | {time_str}")
            
            print("\n" + "=" * 60)
            print("✅ Анализ завершен!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения анализа: {e}")
            print(f"❌ Ошибка: {e}")

def main():
    """Основная функция"""
    analyzer = BTCTradeAnalyzer()
    
    # Анализируем последние 50 сделок
    analyzer.run_analysis(limit=50)

if __name__ == "__main__":
    main() 