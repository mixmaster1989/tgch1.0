#!/usr/bin/env python3
"""
Тест уведомлений в Telegram для попыток покупки
"""

import asyncio
import logging
from datetime import datetime
from market_scanner import MarketScanner

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_telegram_notifications():
    """Тест уведомлений в Telegram"""
    try:
        print("📱 ТЕСТ УВЕДОМЛЕНИЙ В TELEGRAM")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем сканер
        scanner = MarketScanner()
        
        print("🧪 ТЕСТИРУЕМ РАЗЛИЧНЫЕ СЦЕНАРИИ:")
        print()
        
        # Тест 1: Недостаточно средств
        print("1️⃣ Тест: Недостаточно средств")
        insufficient_opportunities = [
            {
                'symbol': 'BTCUSDT',
                'score': 8,
                'rsi': 25.0,
                'reasons': ['перепродано', 'низкий_rsi', 'macd_buy']
            }
        ]
        
        scan_results_insufficient = {
            'buy_opportunities': insufficient_opportunities,
            'total_pairs': 200,
            'analyzed_pairs': 200
        }
        
        # Симулируем недостаток средств (временно изменяем метод)
        original_get_balance = scanner.get_usdt_balance
        scanner.get_usdt_balance = lambda: 5.0  # $5 вместо реального баланса
        
        await scanner.auto_buy_opportunities(scan_results_insufficient)
        
        # Восстанавливаем оригинальный метод
        scanner.get_usdt_balance = original_get_balance
        
        print("✅ Уведомление о недостатке средств отправлено")
        print()
        
        # Тест 2: Малая сумма покупки
        print("2️⃣ Тест: Малая сумма покупки")
        small_amount_opportunities = [
            {
                'symbol': 'ETHUSDT',
                'score': 7,
                'rsi': 28.0,
                'reasons': ['перепродано', 'bb_нижняя', 'высокий_объем']
            }
        ]
        
        scan_results_small = {
            'buy_opportunities': small_amount_opportunities,
            'total_pairs': 200,
            'analyzed_pairs': 200
        }
        
        # Симулируем малый баланс
        scanner.get_usdt_balance = lambda: 15.0  # $15 (30% = $4.5 < $5)
        
        await scanner.auto_buy_opportunities(scan_results_small)
        
        # Восстанавливаем оригинальный метод
        scanner.get_usdt_balance = original_get_balance
        
        print("✅ Уведомление о малой сумме отправлено")
        print()
        
        # Тест 3: Начало покупки
        print("3️⃣ Тест: Начало покупки")
        good_opportunities = [
            {
                'symbol': 'ADAUSDT',
                'score': 6,
                'rsi': 32.0,
                'reasons': ['перепродано', 'низкий_rsi', 'нормальный_объем']
            }
        ]
        
        scan_results_good = {
            'buy_opportunities': good_opportunities,
            'total_pairs': 200,
            'analyzed_pairs': 200
        }
        
        # Симулируем достаточный баланс
        scanner.get_usdt_balance = lambda: 50.0  # $50 (30% = $15 > $5)
        
        await scanner.auto_buy_opportunities(scan_results_good)
        
        # Восстанавливаем оригинальный метод
        scanner.get_usdt_balance = original_get_balance
        
        print("✅ Уведомление о начале покупки отправлено")
        print()
        
        print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        print("📱 Проверьте Telegram для уведомлений")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        logger.error(f"Ошибка теста: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram_notifications()) 