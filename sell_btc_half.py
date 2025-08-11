#!/usr/bin/env python3
"""
Продажа половины BTC для балансировки портфеля
"""

from mex_api import MexAPI
from portfolio_balancer import PortfolioBalancer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sell_half_btc():
    """Продать половину BTC для балансировки"""
    try:
        api = MexAPI()
        balancer = PortfolioBalancer()
        
        # Получаем текущий баланс BTC
        balances = balancer.get_portfolio_balances()
        print('=== ТЕКУЩИЙ ПОРТФЕЛЬ ===')
        for asset, data in balances.items():
            print(f'{asset}: {data["total"]} (свободно: {data["free"]})')
        
        if 'BTC' not in balances:
            print('❌ BTC не найден в портфеле!')
            return
            
        btc_total = balances['BTC']['total']
        btc_free = balances['BTC']['free']
        sell_quantity = btc_total / 2  # Половина
        
        print(f'\n=== ПЛАН ПРОДАЖИ ===')
        print(f'Всего BTC: {btc_total:.6f}')
        print(f'Свободно BTC: {btc_free:.6f}')
        print(f'Продать: {sell_quantity:.6f} BTC')
        
        if sell_quantity > btc_free:
            print(f'❌ Недостаточно свободного BTC! Нужно: {sell_quantity:.6f}, доступно: {btc_free:.6f}')
            return
            
        # Получаем стакан
        print('\n=== СТАКАН BTCUSDC ===')
        orderbook = api.get_depth('BTCUSDC', 10)
        
        if 'bids' not in orderbook or 'asks' not in orderbook:
            print('❌ Ошибка получения стакана')
            return
            
        best_bid = float(orderbook['bids'][0][0])
        best_ask = float(orderbook['asks'][0][0])
        spread = best_ask - best_bid
        spread_percent = (spread / best_bid) * 100
        
        print(f'Лучшая покупка: ${best_bid:.2f}')
        print(f'Лучшая продажа: ${best_ask:.2f}')
        print(f'Спред: ${spread:.2f} ({spread_percent:.3f}%)')
        
        # Цена продажи - чуть выше лучшей покупки для быстрого исполнения
        sell_price = best_bid * 1.0002  # +0.02% для мейкера
        expected_usdc = sell_quantity * sell_price
        
        print(f'\n=== ОРДЕР НА ПРОДАЖУ ===')
        print(f'Цена продажи: ${sell_price:.2f}')
        print(f'Количество: {sell_quantity:.6f} BTC')
        print(f'Получим USDC: ${expected_usdc:.2f}')
        
        # Подтверждение
        confirm = input('\n🤔 Выставить ордер? (yes/no): ')
        if confirm.lower() not in ['yes', 'y', 'да', 'д']:
            print('❌ Отменено пользователем')
            return
            
        # Размещаем ордер
        print('\n🚀 Размещаю ордер на продажу...')
        
        order = api.place_order(
            symbol='BTCUSDC',
            side='SELL',
            quantity=sell_quantity,
            price=sell_price
        )
        
        if 'orderId' in order:
            print(f'✅ ОРДЕР РАЗМЕЩЕН УСПЕШНО!')
            print(f'🆔 ID ордера: {order["orderId"]}')
            print(f'💰 Продаем: {sell_quantity:.6f} BTC')
            print(f'💵 По цене: ${sell_price:.2f}')
            print(f'💎 Получим: ${expected_usdc:.2f} USDC')
            print(f'\n🎯 Теперь можно будет купить ETH на полученные USDC!')
        else:
            print(f'❌ ОШИБКА РАЗМЕЩЕНИЯ ОРДЕРА: {order}')
            
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        logger.error(f'Ошибка продажи BTC: {e}')

if __name__ == "__main__":
    sell_half_btc() 