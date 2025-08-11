#!/usr/bin/env python3
"""
Тест анти-хайп фильтра на реальных данных
"""

from anti_hype_filter import AntiHypeFilter
from balance_monitor import BalanceMonitor
from alt_monitor import AltsMonitor

def test_btc_eth_filter():
    print("🔍 ТЕСТ АНТИ-ХАЙП ФИЛЬТРА ДЛЯ BTC/ETH")
    print("="*60)
    
    filter = AntiHypeFilter()
    
    # Тестируем BTC и ETH
    symbols = ['BTCUSDC', 'ETHUSDC']
    
    for symbol in symbols:
        print(f"\n📊 Анализ {symbol}:")
        result = filter.check_buy_permission(symbol)
        
        status = "✅ РАЗРЕШЕНО" if result['allowed'] else "🚫 ЗАБЛОКИРОВАНО"
        multiplier = f"×{result['multiplier']}" if result['multiplier'] != 1.0 else ""
        
        print(f"   {status} {multiplier}")
        print(f"   Причина: {result['reason']}")
        print(f"   Множитель: {result['multiplier']}")

def test_alts_filter():
    print("\n🧩 ТЕСТ АНТИ-ХАЙП ФИЛЬТРА ДЛЯ АЛЬТОВ")
    print("="*60)
    
    filter = AntiHypeFilter()
    
    # Тестируем топ-5 альтов
    alts = ['BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT']
    
    for symbol in alts:
        print(f"\n📊 Анализ {symbol}:")
        result = filter.check_buy_permission(symbol)
        
        status = "✅ РАЗРЕШЕНО" if result['allowed'] else "🚫 ЗАБЛОКИРОВАНО"
        multiplier = f"×{result['multiplier']}" if result['multiplier'] != 1.0 else ""
        
        print(f"   {status} {multiplier}")
        print(f"   Причина: {result['reason']}")
        print(f"   Множитель: {result['multiplier']}")

def test_balance_monitor_integration():
    print("\n💰 ТЕСТ ИНТЕГРАЦИИ С BALANCE MONITOR")
    print("="*60)
    
    monitor = BalanceMonitor()
    
    # Тестируем расчет покупки с фильтром
    available_amount = 20.0  # $20 USDC
    
    print(f"💰 Доступно для покупки: ${available_amount}")
    
    # Получаем план покупки (с фильтром)
    purchase_plan = monitor.calculate_purchase_amounts(available_amount, 'USDC')
    
    if purchase_plan:
        print(f"📋 План покупки:")
        for symbol, data in purchase_plan.items():
            filter_info = ""
            if 'filter_reason' in data:
                filter_info = f" [{data['filter_reason']}]"
                if data.get('filter_multiplier', 1.0) != 1.0:
                    filter_info += f" ×{data['filter_multiplier']}"
            
            print(f"   {symbol}: ${data['amount']:.2f}{filter_info}")
    else:
        print("❌ Нет подходящих покупок")

def test_alt_monitor_integration():
    print("\n🧩 ТЕСТ ИНТЕГРАЦИИ С ALT MONITOR")
    print("="*60)
    
    # Создаем экземпляр монитора альтов
    alt_monitor = AltsMonitor()
    
    # Получаем балансы
    balances = alt_monitor._get_balances()
    usdt_balance = balances.get('USDT', {}).get('free', 0.0)
    
    print(f"💚 Доступно USDT: ${usdt_balance:.2f}")
    
    if usdt_balance >= 5.0:
        per_alt = usdt_balance / len(['BNB', 'SOL', 'XRP', 'ADA', 'DOGE'])
        print(f"💰 На каждый альт: ${per_alt:.2f}")
        
        # Тестируем фильтр для каждого альта
        for alt in ['BNB', 'SOL', 'XRP', 'ADA', 'DOGE']:
            if alt in balances:
                print(f"   {alt}: уже есть в портфеле")
                continue
                
            symbol = f"{alt}USDT"
            filter_result = alt_monitor.anti_hype_filter.check_buy_permission(symbol)
            
            if filter_result['allowed']:
                adjusted_amount = per_alt * filter_result['multiplier']
                multiplier_text = f" (×{filter_result['multiplier']})" if filter_result['multiplier'] != 1.0 else ""
                print(f"   ✅ {alt}: ${adjusted_amount:.2f}{multiplier_text} [{filter_result['reason']}]")
            else:
                print(f"   🚫 {alt}: заблокировано [{filter_result['reason']}]")
    else:
        print("⚠️ Недостаточно USDT для покупки альтов")

def main():
    print("🧪 ТЕСТИРОВАНИЕ АНТИ-ХАЙП ФИЛЬТРА НА РЕАЛЬНЫХ ДАННЫХ")
    print("="*80)
    
    try:
        # Тест фильтра для BTC/ETH
        test_btc_eth_filter()
        
        # Тест фильтра для альтов
        test_alts_filter()
        
        # Тест интеграции с balance monitor
        test_balance_monitor_integration()
        
        # Тест интеграции с alt monitor
        test_alt_monitor_integration()
        
        print("\n" + "="*80)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()