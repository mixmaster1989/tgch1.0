import logging
from pybitget import Client

class BitgetAPI:
    def __init__(self, api_key, api_secret, api_passphrase):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.client = Client(api_key, api_secret, passphrase=api_passphrase)

    def open_order(self, symbol, side, profile):
        # profile должен содержать параметры: size, leverage, tp, sl и т.д.
        try:
            order_type = profile.get('order_type', 'market')
            size = profile.get('size', 0.01)
            leverage = profile.get('leverage', 20)
            tp = profile.get('tp')
            sl = profile.get('sl')
            # Bitget: productType='UMCBL' для USDT perpetual
            params = {
                'symbol': symbol,
                'marginCoin': 'USDT',
                'size': size,
                'side': side,
                'orderType': order_type,
                'leverage': leverage,
            }
            if tp:
                params['presetTakeProfitPrice'] = tp
            if sl:
                params['presetStopLossPrice'] = sl
            logging.info(f"BitgetAPI: Открытие ордера {params}")
            result = self.client.mix_place_order(productType='UMCBL', **params)
            logging.info(f"BitgetAPI: Ответ на открытие ордера: {result}")
            return result
        except Exception as e:
            logging.error(f"BitgetAPI: Ошибка открытия ордера: {e}")
            return None

    def close_order(self, symbol, side, size=None):
        try:
            params = {
                'symbol': symbol,
                'marginCoin': 'USDT',
                'side': side,
                'orderType': 'market',
            }
            if size is not None:
                params['size'] = size
            else:
                params['size'] = 0  # 0 = close all
            logging.info(f"BitgetAPI: Закрытие ордера {params}")
            result = self.client.mix_close_position(productType='UMCBL', **params)
            logging.info(f"BitgetAPI: Ответ на закрытие ордера: {result}")
            return result
        except Exception as e:
            logging.error(f"BitgetAPI: Ошибка закрытия ордера: {e}")
            return None

    def get_positions(self):
        try:
            result = self.client.mix_get_positions(productType='UMCBL')
            positions = result.get('data', [])
            logging.info(f"BitgetAPI: Позиции: {positions}")
            return positions
        except Exception as e:
            logging.error(f"BitgetAPI: Ошибка получения позиций: {e}")
            return []

    def get_balance(self):
        try:
            result = self.client.mix_get_accounts(productType='UMCBL')
            accounts = result.get('data', [])
            logging.info(f"BitgetAPI: Баланс: {accounts}")
            return accounts
        except Exception as e:
            logging.error(f"BitgetAPI: Ошибка получения баланса: {e}")
            return [] 