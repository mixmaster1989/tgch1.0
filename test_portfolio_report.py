#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отчета портфеля с балансами USDT/USDC
"""

from pnl_monitor import PnLMonitor
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_portfolio_report():
    """Тестируем обновленный отчет портфеля"""
    try:
        logger.info("🧪 Запуск теста отчета портфеля...")
        
        # Создаем экземпляр монитора
        monitor = PnLMonitor()
        
        # Получаем балансы
        logger.info("📊 Получаем балансы...")
        balances = monitor.get_balances()
        logger.info(f"📋 Найденные активы: {list(balances.keys())}")
        
        # Получаем информацию об аккаунте для стабильных монет
        logger.info("🏦 Получаем информацию об аккаунте...")
        account_info = monitor.mex_api.get_account_info()
        
        usdt_balance = 0.0
        usdc_balance = 0.0
        
        if account_info and 'balances' in account_info:
            for balance in account_info['balances']:
                asset = balance['asset']
                total = float(balance.get('free', 0)) + float(balance.get('locked', 0))
                
                if asset == 'USDT' and total > 0:
                    usdt_balance = total
                    logger.info(f"💰 USDT баланс: ${total:.2f}")
                elif asset == 'USDC' and total > 0:
                    usdc_balance = total
                    logger.info(f"💰 USDC баланс: ${total:.2f}")
        
        # Собираем данные для отчета
        pnl_data = []
        portfolio_value = 0.0
        
        # Проверяем BTC и ETH
        for asset in ['BTC', 'ETH']:
            if asset in balances:
                quantity = balances[asset]['total']
                if quantity > 0:
                    symbol = 'BTCUSDC' if asset == 'BTC' else 'ETHUSDC'
                    current_price = monitor.get_current_price(symbol)
                    
                    if current_price:
                        # Упрощенный расчет PnL для теста
                        pnl = 0.0  # В тесте используем 0
                        
                        pnl_data.append({
                            'asset': asset,
                            'quantity': quantity,
                            'current_price': current_price,
                            'pnl': pnl
                        })
                        
                        portfolio_value += quantity * current_price
                        
                        logger.info(f"📊 {asset}: {quantity:.6f} @ ${current_price:.4f}")
        
        # Формируем тестовый отчет
        total_portfolio = portfolio_value + usdt_balance + usdc_balance
        
        message_lines = [
            "📊 <b>ПОРТФЕЛЬ BTC/ETH (ТЕСТ)</b>\n",
            f"💎 <b>СТОИМОСТЬ ПОРТФЕЛЯ</b>: <code>${portfolio_value:.2f}</code>\n",
            f"🏦 <b>ОБЩАЯ СТОИМОСТЬ</b>: <code>${total_portfolio:.2f}</code>\n\n",
            f"💵 <b>СТАБИЛЬНЫЕ МОНЕТЫ:</b>\n",
            f"   💰 USDT: ${usdt_balance:.2f}\n",
            f"   💰 USDC: ${usdc_balance:.2f}\n\n"
        ]
        
        for item in pnl_data:
            pnl_status = "📈" if item['pnl'] > 0 else "📉" if item['pnl'] < 0 else "➡️"
            message_lines.append(
                f"{pnl_status} <b>{item['asset']}</b>:\n"
                f"   📊 {item['quantity']:.6f} @ ${item['current_price']:.4f}\n"
                f"   💵 PnL: ${item['pnl']:.4f} (порог: $0.07)\n\n"
            )
        
        message_lines.append("🧪 <b>ТЕСТОВЫЙ ОТЧЕТ</b>")
        
        # Выводим результат
        test_report = "".join(message_lines)
        print("\n" + "="*50)
        print("ТЕСТОВЫЙ ОТЧЕТ ПОРТФЕЛЯ:")
        print("="*50)
        print(test_report)
        print("="*50)
        
        logger.info("✅ Тест отчета портфеля завершен успешно!")
        
        # Отправляем тестовый отчет в Telegram (опционально)
        # monitor.send_telegram_message(test_report)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте: {e}")
        return False

if __name__ == "__main__":
    test_portfolio_report()

