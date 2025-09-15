import asyncio
from active_50_50_balancer import Active5050Balancer

async def run_balance():
    balancer = Active5050Balancer()
    
    print("🚀 ЗАПУСК БАЛАНСИРОВКИ ПОРТФЕЛЯ 50/50")
    print("=" * 50)
    
    # Получаем текущее состояние портфеля
    portfolio = balancer.get_portfolio_values()
    print(f"📊 ТЕКУЩЕЕ СОСТОЯНИЕ:")
    print(f"   Альты: ${portfolio['alts_value']:.2f} ({portfolio['alts_value']/portfolio['total_value']*100:.1f}%)")
    print(f"   BTC/ETH: ${portfolio['btceth_value_usdt']:.2f} ({portfolio['btceth_value_usdt']/portfolio['total_value']*100:.1f}%)")
    print(f"   Общая стоимость: ${portfolio['total_value']:.2f}")
    print()
    
    # Проверяем балансы
    usdc = balancer.get_usdc_balance()
    usdt = balancer.get_usdt_balance()
    print(f"💰 СТЕЙБЛКОИНЫ:")
    print(f"   USDC: ${usdc:.2f}")
    print(f"   USDT: ${usdt:.2f}")
    print(f"   ОБЩИЙ: ${usdc + usdt:.2f}")
    print()
    
    # Запускаем балансировку
    print("⚖️ ВЫПОЛНЯЮ БАЛАНСИРОВКУ...")
    result = await balancer.balance_cycle()
    
    if result:
        print("✅ БАЛАНСИРОВКА ВЫПОЛНЕНА УСПЕШНО!")
        
        # Показываем результат
        portfolio_after = balancer.get_portfolio_values()
        print(f"📊 РЕЗУЛЬТАТ:")
        print(f"   Альты: ${portfolio_after['alts_value']:.2f} ({portfolio_after['alts_value']/portfolio_after['total_value']*100:.1f}%)")
        print(f"   BTC/ETH: ${portfolio_after['btceth_value_usdt']:.2f} ({portfolio_after['btceth_value_usdt']/portfolio_after['total_value']*100:.1f}%)")
        print(f"   Общая стоимость: ${portfolio_after['total_value']:.2f}")
    else:
        print("❌ БАЛАНСИРОВКА НЕ ВЫПОЛНЕНА!")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_balance())
