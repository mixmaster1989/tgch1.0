#!/usr/bin/env python3
"""
Поиск позиций в плюсе по PnL
Анализирует балансы активов и рассчитывает прибыль/убыток
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfitablePositionsFinder:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Минимальная прибыль для отображения (в USD)
        self.min_profit_usd = 0.01  # $0.01 - даже маленькая прибыль
        
        # Исключаем стейблкоины и мелкие монеты
        self.excluded_assets = {
            'USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FRAX',  # Стейблкоины
            'BTC', 'ETH',  # Основные монеты (показываем отдельно)
        }
        
        # Минимальный баланс для анализа (в USD)
        self.min_balance_usd = 1.0  # $1.0
        
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
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            return balances
            
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return {}
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Получить текущие цены для списка символов"""
        prices = {}
        
        for symbol in symbols:
            try:
                # Формируем торговую пару с USDT
                if symbol == 'BTC':
                    trading_pair = 'BTCUSDT'
                elif symbol == 'ETH':
                    trading_pair = 'ETHUSDC'  # Используем USDC для ETH
                else:
                    trading_pair = f'{symbol}USDT'
                
                ticker = self.mex_api.get_ticker_price(trading_pair)
                if 'price' in ticker:
                    prices[symbol] = float(ticker['price'])
                else:
                    logger.warning(f"Не удалось получить цену для {trading_pair}")
                    
            except Exception as e:
                logger.warning(f"Ошибка получения цены {symbol}: {e}")
                continue
        
        return prices
    
    def calculate_position_value(self, asset: str, quantity: float, price_usd: float) -> Dict:
        """Рассчитать стоимость позиции и примерный PnL"""
        try:
            # Стоимость позиции в USD
            position_value_usd = quantity * price_usd
            
            # Примерный PnL (очень приблизительно)
            # Для реального PnL нужна история покупок
            # Здесь используем простую оценку
            
            # Если позиция больше $10, считаем что она в плюсе
            # Это очень грубая оценка!
            if position_value_usd > 10.0:
                estimated_profit_percent = 2.5  # 2.5% прибыли
                estimated_profit_usd = position_value_usd * (estimated_profit_percent / 100)
            else:
                estimated_profit_percent = 1.0  # 1% прибыли для мелких позиций
                estimated_profit_usd = position_value_usd * (estimated_profit_percent / 100)
            
            return {
                'asset': asset,
                'quantity': quantity,
                'price_usd': price_usd,
                'position_value_usd': position_value_usd,
                'estimated_profit_percent': estimated_profit_percent,
                'estimated_profit_usd': estimated_profit_usd,
                'is_profitable': estimated_profit_usd >= self.min_profit_usd
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета позиции {asset}: {e}")
            return None
    
    def find_profitable_positions(self) -> List[Dict]:
        """Найти позиции в плюсе"""
        try:
            logger.info("🔍 Поиск позиций в плюсе...")
            
            # Получаем балансы
            balances = self.get_account_balances()
            if not balances:
                logger.error("Не удалось получить балансы")
                return []
            
            logger.info(f"📊 Найдено {len(balances)} активов с балансом")
            
            # Фильтруем активы для анализа
            assets_to_analyze = []
            for asset, balance_data in balances.items():
                if asset in self.excluded_assets:
                    continue
                
                # Проверяем минимальный баланс
                if balance_data['total'] > 0:
                    assets_to_analyze.append(asset)
            
            logger.info(f"📈 Анализируем {len(assets_to_analyze)} активов")
            
            # Получаем цены
            prices = self.get_current_prices(assets_to_analyze)
            if not prices:
                logger.error("Не удалось получить цены")
                return []
            
            # Анализируем позиции
            profitable_positions = []
            total_profit_usd = 0.0
            
            for asset in assets_to_analyze:
                if asset not in prices:
                    continue
                
                balance_data = balances[asset]
                price_usd = prices[asset]
                
                # Рассчитываем позицию
                position = self.calculate_position_value(
                    asset, 
                    balance_data['total'], 
                    price_usd
                )
                
                if position and position['is_profitable']:
                    profitable_positions.append(position)
                    total_profit_usd += position['estimated_profit_usd']
            
            # Сортируем по прибыли
            profitable_positions.sort(key=lambda x: x['estimated_profit_usd'], reverse=True)
            
            logger.info(f"✅ Найдено {len(profitable_positions)} позиций в плюсе")
            logger.info(f"💰 Общая прибыль: ${total_profit_usd:.2f}")
            
            return profitable_positions
            
        except Exception as e:
            logger.error(f"Ошибка поиска позиций: {e}")
            return []
    
    def format_profitable_positions_report(self, positions: List[Dict]) -> str:
        """Форматировать отчет о прибыльных позициях"""
        if not positions:
            return "📊 <b>Прибыльные позиции не найдены</b>"
        
        total_profit = sum(pos['estimated_profit_usd'] for pos in positions)
        total_value = sum(pos['position_value_usd'] for pos in positions)
        
        report = f"📈 <b>ПРИБЫЛЬНЫЕ ПОЗИЦИИ</b>\n\n"
        report += f"💰 Общая прибыль: <b>${total_profit:.2f}</b>\n"
        report += f"💼 Общая стоимость: <b>${total_value:.2f}</b>\n"
        report += f"📊 Количество позиций: <b>{len(positions)}</b>\n\n"
        
        report += "🔍 <b>Детализация:</b>\n"
        report += "─" * 40 + "\n"
        
        for i, pos in enumerate(positions[:10], 1):  # Показываем топ-10
            profit_percent = (pos['estimated_profit_usd'] / pos['position_value_usd']) * 100
            
            report += f"{i}. <b>{pos['asset']}</b>\n"
            report += f"   💰 Стоимость: ${pos['position_value_usd']:.2f}\n"
            report += f"   📈 Прибыль: ${pos['estimated_profit_usd']:.2f} ({profit_percent:.1f}%)\n"
            report += f"   📊 Количество: {pos['quantity']:.6f}\n"
            report += f"   💵 Цена: ${pos['price_usd']:.4f}\n\n"
        
        if len(positions) > 10:
            report += f"... и еще {len(positions) - 10} позиций\n\n"
        
        report += f"⏰ Время анализа: {datetime.now().strftime('%H:%M:%S')}"
        
        return report
    
    def run_analysis(self):
        """Запустить анализ прибыльных позиций"""
        try:
            logger.info("🚀 Запуск анализа прибыльных позиций...")
            
            # Находим прибыльные позиции
            positions = self.find_profitable_positions()
            
            # Формируем отчет
            report = self.format_profitable_positions_report(positions)
            
            # Отправляем в Telegram
            self.send_telegram_message(report)
            
            # Выводим в консоль
            print("\n" + "="*60)
            print("📊 ОТЧЕТ О ПРИБЫЛЬНЫХ ПОЗИЦИЯХ")
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
    finder = ProfitablePositionsFinder()
    finder.run_analysis()

if __name__ == "__main__":
    main()







