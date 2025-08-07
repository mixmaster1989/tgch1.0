#!/usr/bin/env python3
"""
Тест расширенного MEX API
Проверяем: правила торговли, историю сделок, комиссии
"""

import json
from mexc_advanced_api import MexAdvancedAPI

def test_exchange_info():
    """Тест получения информации о бирже"""
    print("🔍 Тест получения exchange info...")
    
    api = MexAdvancedAPI()
    exchange_info = api.get_exchange_info()
    
    if exchange_info and 'symbols' in exchange_info:
        print(f"✅ Получено {len(exchange_info['symbols'])} торговых пар")
        
        # Показываем примеры пар
        usdt_pairs = [s for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]
        print(f"📊 USDT пар: {len(usdt_pairs)}")
        
        # Показываем первые 3 пары
        for i, symbol in enumerate(usdt_pairs[:3]):
            print(f"  {i+1}. {symbol['symbol']} - {symbol['status']}")
    else:
        print("❌ Ошибка получения exchange info")

def test_symbol_rules():
    """Тест получения правил торговли"""
    print("\n🔍 Тест получения правил торговли...")
    
    api = MexAdvancedAPI()
    symbols = ['ETHUSDT', 'BTCUSDT', 'ADAUSDT']
    
    for symbol in symbols:
        print(f"\n📋 Правила для {symbol}:")
        rules = api.get_symbol_rules(symbol)
        
        if rules:
            print(f"  ✅ Статус: {rules.get('status', 'UNKNOWN')}")
            print(f"  📏 Минимальный лот: {rules.get('minQty', 0)}")
            print(f"  💰 Минимальная сумма: ${rules.get('minNotional', 0)}")
            print(f"  🎯 Точность цены: {rules.get('pricePrecision', 8)} знаков")
            print(f"  📊 Точность количества: {rules.get('quantityPrecision', 8)} знаков")
        else:
            print(f"  ❌ Не удалось получить правила")

def test_trade_fees():
    """Тест получения комиссий"""
    print("\n🔍 Тест получения комиссий...")
    
    api = MexAdvancedAPI()
    fee_data = api.get_trade_fee()
    
    if fee_data and 'tradeFee' in fee_data:
        print(f"✅ Получены комиссии для {len(fee_data['tradeFee'])} пар")
        
        # Показываем комиссии для ETHUSDT
        eth_fee = api.get_symbol_fee('ETHUSDT')
        print(f"📊 Комиссии ETHUSDT:")
        print(f"  🟢 Maker: {eth_fee.get('makerCommissionRate', 0)*100:.3f}%")
        print(f"  🔴 Taker: {eth_fee.get('takerCommissionRate', 0)*100:.3f}%")
    else:
        print("❌ Ошибка получения комиссий")

def test_min_order_size():
    """Тест расчета минимального размера ордера"""
    print("\n🔍 Тест расчета минимального размера ордера...")
    
    api = MexAdvancedAPI()
    symbols = ['ETHUSDT', 'BTCUSDT']
    
    for symbol in symbols:
        print(f"\n📏 Минимальный размер для {symbol}:")
        
        # Получаем текущую цену (примерная)
        current_price = 3728.60 if symbol == 'ETHUSDT' else 114000.0
        
        min_order = api.calculate_min_order_size(symbol, current_price)
        
        if min_order:
            print(f"  💰 Минимальный лот: {min_order.get('min_qty', 0)}")
            print(f"  💵 Минимальная сумма: ${min_order.get('min_notional', 0)}")
            print(f"  🎯 Минимальный ордер: ${min_order.get('min_order_usdt', 0):.2f}")
            print(f"  📊 Точность цены: {min_order.get('price_precision', 8)} знаков")
            print(f"  🟢 Maker комиссия: {min_order.get('maker_fee', 0)*100:.3f}%")
            print(f"  🔴 Taker комиссия: {min_order.get('taker_fee', 0)*100:.3f}%")
        else:
            print(f"  ❌ Ошибка расчета")

def test_my_trades():
    """Тест получения истории сделок"""
    print("\n🔍 Тест получения истории сделок...")
    
    api = MexAdvancedAPI()
    trades = api.get_my_trades('ETHUSDT', limit=10)
    
    if trades:
        print(f"✅ Получено {len(trades)} сделок")
        
        if len(trades) > 0:
            print("📊 Последние сделки:")
            for i, trade in enumerate(trades[:3]):
                side = "🟢 BUY" if trade['isBuyer'] else "🔴 SELL"
                print(f"  {i+1}. {side} {trade['qty']} ETH по ${trade['price']:.2f}")
                print(f"     💰 Сумма: ${trade['quoteQty']:.2f}")
                print(f"     💸 Комиссия: {trade['commission']} {trade['commissionAsset']}")
    else:
        print("ℹ️ Нет сделок или ошибка получения")

def test_trading_summary():
    """Тест получения сводки по торговле"""
    print("\n🔍 Тест получения сводки по торговле...")
    
    api = MexAdvancedAPI()
    summary = api.get_trading_summary('ETHUSDT')
    
    if summary:
        print("📊 Сводка по торговле ETHUSDT:")
        print(f"  📈 Всего сделок: {summary.get('total_trades', 0)}")
        print(f"  🟢 Объем покупок: {summary.get('total_buy_volume', 0):.4f} ETH")
        print(f"  🔴 Объем продаж: {summary.get('total_sell_volume', 0):.4f} ETH")
        print(f"  📊 Текущая позиция: {summary.get('current_position', 0):.4f} ETH")
        print(f"  💸 Общие комиссии: {summary.get('total_commission', 0):.4f}")
        print(f"  💰 Реализованный P&L: ${summary.get('realized_pnl', 0):.2f}")
        
        if summary.get('avg_buy_price', 0) > 0:
            print(f"  📈 Средняя цена покупки: ${summary.get('avg_buy_price', 0):.2f}")
        if summary.get('avg_sell_price', 0) > 0:
            print(f"  📉 Средняя цена продажи: ${summary.get('avg_sell_price', 0):.2f}")
    else:
        print("ℹ️ Нет данных для сводки")

def main():
    """Основной тест"""
    print("🚀 ТЕСТ РАСШИРЕННОГО MEX API")
    print("=" * 50)
    
    try:
        test_exchange_info()
        test_symbol_rules()
        test_trade_fees()
        test_min_order_size()
        test_my_trades()
        test_trading_summary()
        
        print("\n" + "=" * 50)
        print("✅ Тест расширенного API завершен!")
        
    except Exception as e:
        print(f"\n❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
