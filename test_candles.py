#!/usr/bin/env python3
"""
Тест получения свечей по разным парам
"""

from mex_api import MexAPI
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_candles():
    api = MexAPI()
    
    # Тестируем разные пары
    test_pairs = [
        'BTCUSDC', 'ETHUSDC', 'BTCUSDT', 'ETHUSDT',
        'BNBUSDC', 'ADAUSDC', 'SOLUSDC', 'BROCKUSDC'
    ]
    
    for pair in test_pairs:
        try:
            logger.info(f"🔍 Тестирую получение свечей для {pair}...")
            
            # Пробуем получить часовые свечи
            klines = api.get_klines(pair, '60m', 1)
            
            if klines and len(klines) > 0:
                candle = klines[0]
                logger.info(f"✅ {pair}: Свечи доступны")
                logger.info(f"   Открытие: ${float(candle[1]):.4f}")
                logger.info(f"   Максимум: ${float(candle[2]):.4f}")
                logger.info(f"   Минимум: ${float(candle[3]):.4f}")
                logger.info(f"   Закрытие: ${float(candle[4]):.4f}")
            else:
                logger.warning(f"⚠️ {pair}: Свечи недоступны или пустые")
                
        except Exception as e:
            logger.error(f"❌ {pair}: Ошибка получения свечей - {e}")

if __name__ == "__main__":
    test_candles() 