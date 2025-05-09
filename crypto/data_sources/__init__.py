"""
Пакет для работы с источниками данных о криптовалютах
"""

# Ленивый импорт для предотвращения проблем с циклическими зависимостями

def __getattr__(name):
    if name == 'CryptoDataManager':
        from .crypto_data_manager import CryptoDataManager
        return CryptoDataManager
    elif name == 'get_data_manager':
        from .crypto_data_manager import get_data_manager
        return get_data_manager
    elif name == 'CryptorankAPI':
        from .cryptorank_api import CryptorankAPI
        return CryptorankAPI

__all__ = ['CryptoDataManager', 'get_data_manager', 'CryptorankAPI']