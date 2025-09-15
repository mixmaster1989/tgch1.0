#!/usr/bin/env python3
"""
Детальный анализ ордеров BTCUSDC
Проверяем комиссии, исполнение и детали конкретных сделок
"""

import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional
from mex_api import MexAPI

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BTCOrderAnalyzer:
    """Детальный анализатор ордеров BTCUSDC"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.symbol = 'BTCUSDC'
        
    def get_order_details(self, order_id: int) -> Dict:
        """Получить детали конкретного ордера"""
        try:
            logger.info(f"🔍 Получаем детали ордера {order_id}...")
            
            # Получаем информацию об ордере
            timestamp = int(datetime.now().timestamp() * 1000)
            query_string = f'symbol={self.symbol}&orderId={order_id}&timestamp={timestamp}'
            
            # Генерируем подпись
            signature = self.mex_api._generate_signature(query_string)
            url = f"{self.mex_api.base_url}/api/v3/order?{query_string}&signature={signature}"
            
            response = self.mex_api._make_request_with_retry('GET', url, headers=self.mex_api._get_headers(True))
            
            if response and 'orderId' in response:
                logger.info(f"✅ Получены детали ордера {order_id}")
                return response
            else:
                logger.error(f"❌ Ошибка получения ордера {order_id}: {response}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения деталей ордера: {e}")
            return {}
    
    def analyze_order_execution(self, order: Dict) -> Dict:
        """Анализ исполнения ордера"""
        try:
            if not order:
                return {}
            
            order_id = order.get('orderId', 'N/A')
            side = order.get('side', 'N/A')
            status = order.get('status', 'N/A')
            symbol = order.get('symbol', 'N/A')
            
            # Основные параметры
            orig_qty = float(order.get('origQty', 0))
            executed_qty = float(order.get('executedQty', 0))
            cummulative_quote_qty = float(order.get('cummulativeQuoteQty', 0))
            
            # Цены
            price = float(order.get('price', 0))
            avg_price = float(order.get('avgPrice', 0)) if order.get('avgPrice') else 0
            
            # Комиссии
            commission = float(order.get('commission', 0))
            commission_asset = order.get('commissionAsset', 'N/A')
            
            # Время
            time_ms = int(order.get('time', 0))
            update_time_ms = int(order.get('updateTime', 0))
            
            time_str = datetime.fromtimestamp(time_ms/1000).strftime('%d.%m.%Y %H:%M:%S')
            update_time_str = datetime.fromtimestamp(update_time_ms/1000).strftime('%d.%m.%Y %H:%M:%S')
            
            # Анализ исполнения
            execution_percent = (executed_qty / orig_qty * 100) if orig_qty > 0 else 0
            remaining_qty = orig_qty - executed_qty
            
            # Расчет эффективной цены
            if executed_qty > 0 and cummulative_quote_qty > 0:
                effective_price = cummulative_quote_qty / executed_qty
            else:
                effective_price = price
            
            return {
                'order_id': order_id,
                'side': side,
                'status': status,
                'symbol': symbol,
                'orig_qty': orig_qty,
                'executed_qty': executed_qty,
                'remaining_qty': remaining_qty,
                'execution_percent': execution_percent,
                'price': price,
                'avg_price': avg_price,
                'effective_price': effective_price,
                'cummulative_quote_qty': cummulative_quote_qty,
                'commission': commission,
                'commission_asset': commission_asset,
                'time': time_str,
                'update_time': update_time_str,
                'time_ms': time_ms,
                'update_time_ms': update_time_ms
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа исполнения ордера: {e}")
            return {}
    
    def format_order_report(self, order_analysis: Dict) -> str:
        """Форматировать отчет об ордере"""
        try:
            if not order_analysis:
                return "❌ Нет данных для анализа"
            
            message = f"<b>📋 ДЕТАЛИ ОРДЕРА {order_analysis['symbol']}</b>\n"
            message += "=" * 50 + "\n\n"
            
            message += f"🆔 ID ордера: {order_analysis['order_id']}\n"
            message += f"📊 Сторона: {order_analysis['side']}\n"
            message += f"📈 Статус: {order_analysis['status']}\n"
            message += f"⏰ Время создания: {order_analysis['time']}\n"
            message += f"🔄 Время обновления: {order_analysis['update_time']}\n\n"
            
            message += "<b>💰 КОЛИЧЕСТВО:</b>\n"
            message += f"   Исходное: {order_analysis['orig_qty']:.6f} BTC\n"
            message += f"   Исполнено: {order_analysis['executed_qty']:.6f} BTC\n"
            message += f"   Осталось: {order_analysis['remaining_qty']:.6f} BTC\n"
            message += f"   Процент исполнения: {order_analysis['execution_percent']:.1f}%\n\n"
            
            message += "<b>💵 ЦЕНЫ:</b>\n"
            message += f"   Указанная цена: ${order_analysis['price']:.2f} USDC\n"
            message += f"   Средняя цена: ${order_analysis['avg_price']:.2f} USDC\n"
            message += f"   Эффективная цена: ${order_analysis['effective_price']:.2f} USDC\n"
            message += f"   Общая стоимость: ${order_analysis['cummulative_quote_qty']:.2f} USDC\n\n"
            
            message += "<b>💸 КОМИССИИ:</b>\n"
            message += f"   Сумма: {order_analysis['commission']:.6f} {order_analysis['commission_asset']}\n"
            
            if order_analysis['commission'] > 0:
                commission_percent = (order_analysis['commission'] / order_analysis['cummulative_quote_qty'] * 100) if order_analysis['cummulative_quote_qty'] > 0 else 0
                message += f"   В % от сделки: {commission_percent:.4f}%\n"
            
            message += "\n" + "=" * 50 + "\n"
            message += "<b>📋 ДЕТАЛИ ОРДЕРА</b>"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования отчета: {e}")
            return f"❌ Ошибка отчета: {e}"
    
    def analyze_recent_orders(self, limit: int = 10) -> None:
        """Анализ последних ордеров"""
        try:
            print(f"🚀 ДЕТАЛЬНЫЙ АНАЛИЗ ОРДЕРОВ {self.symbol}")
            print("=" * 60)
            
            # Получаем историю ордеров
            orders = self.mex_api.get_order_history(symbol=self.symbol, limit=limit)
            
            if not orders or 'code' in orders:
                print("❌ Не удалось получить историю ордеров")
                return
            
            print(f"📊 Получено {len(orders)} ордеров")
            print()
            
            # Анализируем каждый ордер
            for i, order in enumerate(orders, 1):
                order_id = order.get('orderId', 'N/A')
                side = order.get('side', 'N/A')
                status = order.get('status', 'N/A')
                executed_qty = float(order.get('executedQty', 0))
                price = float(order.get('price', 0))
                commission = float(order.get('commission', 0))
                time_str = datetime.fromtimestamp(int(order.get('time', 0))/1000).strftime('%d.%m %H:%M:%S')
                
                print(f"🔍 ОРДЕР #{i}: {order_id}")
                print(f"   Сторона: {side}")
                print(f"   Статус: {status}")
                print(f"   Количество: {executed_qty:.6f} BTC")
                print(f"   Цена: ${price:.2f} USDC")
                print(f"   Комиссия: {commission:.6f}")
                print(f"   Время: {time_str}")
                
                # Если ордер исполнен, получаем детали
                if status == 'FILLED' and executed_qty > 0:
                    print(f"   📋 Получаем детали...")
                    details = self.get_order_details(order_id)
                    if details:
                        analysis = self.analyze_order_execution(details)
                        if analysis:
                            print(f"   ✅ Детали получены")
                            print(f"      Эффективная цена: ${analysis['effective_price']:.2f} USDC")
                            print(f"      Общая стоимость: ${analysis['cummulative_quote_qty']:.2f} USDC")
                            if analysis['commission'] > 0:
                                commission_percent = (analysis['commission'] / analysis['cummulative_quote_qty'] * 100) if analysis['cummulative_quote_qty'] > 0 else 0
                                print(f"      Комиссия: {analysis['commission']:.6f} {analysis['commission_asset']} ({commission_percent:.4f}%)")
                        else:
                            print(f"   ❌ Не удалось проанализировать")
                    else:
                        print(f"   ❌ Не удалось получить детали")
                
                print()
            
            print("=" * 60)
            print("✅ Анализ завершен!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа ордеров: {e}")
            print(f"❌ Ошибка: {e}")

def main():
    """Основная функция"""
    analyzer = BTCOrderAnalyzer()
    
    # Анализируем последние 10 ордеров
    analyzer.analyze_recent_orders(limit=10)

if __name__ == "__main__":
    main() 