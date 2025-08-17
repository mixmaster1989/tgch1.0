#!/usr/bin/env python3
"""
Проверка реального распределения BTC/ETH в портфеле
"""

from mex_api import MexAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_real_allocation():
    """Проверить реальное распределение BTC/ETH"""
    try:
        api = MexAPI()
        
        # Получаем информацию об аккаунте
        account_info = api.get_account_info()
        
        btc_balance = 0.0
        eth_balance = 0.0
        usdc_balance = 0.0
        usdt_balance = 0.0
        
        print("🔍 Проверяем реальные балансы...")
        
        for balance in account_info.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                print(f"   {asset}: {total:.6f} (свободно: {free:.6f}, заблокировано: {locked:.6f})")
                
                if asset == 'BTC':
                    btc_balance = total
                elif asset == 'ETH':
                    eth_balance = total
                elif asset == 'USDC':
                    usdc_balance = total
                elif asset == 'USDT':
                    usdt_balance = total
        
        print(f"\n💰 Балансы стейблкоинов:")
        print(f"   USDC: ${usdc_balance:.2f}")
        print(f"   USDT: ${usdt_balance:.2f}")
        
        # Получаем текущие цены
        btc_price_usdc = api.get_ticker_price('BTCUSDC')
        eth_price_usdc = api.get_ticker_price('ETHUSDC')
        
        if 'price' in btc_price_usdc and 'price' in eth_price_usdc:
            btc_price = float(btc_price_usdc['price'])
            eth_price = float(eth_price_usdc['price'])
            
            # Рассчитываем стоимость в USDC
            btc_value_usdc = btc_balance * btc_price
            eth_value_usdc = eth_balance * eth_price
            
            total_crypto_usdc = btc_value_usdc + eth_value_usdc
            total_portfolio_usdc = total_crypto_usdc + usdc_balance + usdt_balance
            
            print(f"\n📊 РЕАЛЬНОЕ РАСПРЕДЕЛЕНИЕ BTC/ETH:")
            print(f"   BTC: {btc_balance:.6f} × ${btc_price:.2f} = ${btc_value_usdc:.2f}")
            print(f"   ETH: {eth_balance:.6f} × ${eth_price:.2f} = ${eth_value_usdc:.2f}")
            print(f"   Всего крипты: ${total_crypto_usdc:.2f}")
            
            if total_crypto_usdc > 0:
                btc_percent = (btc_value_usdc / total_crypto_usdc) * 100
                eth_percent = (eth_value_usdc / total_crypto_usdc) * 100
                
                print(f"\n🎯 РАСПРЕДЕЛЕНИЕ КРИПТОВАЛЮТ:")
                print(f"   BTC: {btc_percent:.1f}% (должно быть 60%)")
                print(f"   ETH: {eth_percent:.1f}% (должно быть 40%)")
                
                # Проверяем отклонение
                btc_deviation = abs(btc_percent - 60)
                eth_deviation = abs(eth_percent - 40)
                
                print(f"\n⚠️ ОТКЛОНЕНИЕ ОТ ЦЕЛИ:")
                print(f"   BTC: {btc_deviation:.1f}% от нормы")
                print(f"   ETH: {eth_deviation:.1f}% от нормы")
                
                if btc_deviation > 10 or eth_deviation > 10:
                    print(f"\n🚨 ТРЕБУЕТСЯ БАЛАНСИРОВКА!")
                    print(f"   Нужно докупить ETH на ${(total_crypto_usdc * 0.4) - eth_value_usdc:.2f}")
                else:
                    print(f"\n✅ Распределение в норме!")
            
            print(f"\n💼 ОБЩИЙ ПОРТФЕЛЬ:")
            print(f"   Криптовалюты: ${total_crypto_usdc:.2f}")
            print(f"   Стейблкоины: ${usdc_balance + usdt_balance:.2f}")
            print(f"   ВСЕГО: ${total_portfolio_usdc:.2f}")
            
        else:
            print("❌ Не удалось получить цены BTC/ETH")
            
    except Exception as e:
        logger.error(f"Ошибка проверки распределения: {e}")

if __name__ == "__main__":
    check_real_allocation() 