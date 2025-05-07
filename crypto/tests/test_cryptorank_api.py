"""
Тесты для модуля работы с API Cryptorank
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from crypto.data_sources.cryptorank_api import CryptorankAPI

@pytest.fixture
def mock_config():
    """Мок для конфигурации"""
    return {
        'api': {
            'cryptorank': {
                'api_key': 'test_api_key',
                'base_url': 'https://api.cryptorank.io/v1',
                'rate_limit': {
                    'requests_per_minute': 30,
                    'retry_after': 60
                }
            }
        }
    }

@pytest.fixture
def mock_response():
    """Мок для ответа API"""
    mock = MagicMock()
    mock.status = 200
    mock.json = asyncio.coroutine(lambda: {'data': [{'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC'}]})
    return mock

@pytest.fixture
def mock_session():
    """Мок для сессии aiohttp"""
    mock = MagicMock()
    mock.__aenter__ = asyncio.coroutine(lambda *args, **kwargs: mock)
    mock.__aexit__ = asyncio.coroutine(lambda *args, **kwargs: None)
    return mock

@pytest.fixture
def mock_client_session():
    """Мок для ClientSession"""
    mock = MagicMock()
    mock.__aenter__ = asyncio.coroutine(lambda *args, **kwargs: mock)
    mock.__aexit__ = asyncio.coroutine(lambda *args, **kwargs: None)
    return mock

@pytest.mark.asyncio
async def test_get_coins(mock_config, mock_response, mock_session, mock_client_session):
    """Тест получения списка монет"""
    with patch('crypto.data_sources.cryptorank_api.get_config', return_value=mock_config), \
         patch('crypto.data_sources.cryptorank_api.get_cryptorank_api_key', return_value='test_api_key'), \
         patch('aiohttp.ClientSession', return_value=mock_client_session):
        
        # Настраиваем моки
        mock_client_session.get.return_value = mock_session
        mock_session.status = 200
        mock_session.json = asyncio.coroutine(lambda: {'data': [{'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC'}]})
        
        # Создаем экземпляр API
        api = CryptorankAPI()
        
        # Вызываем метод
        coins = await api.get_coins()
        
        # Проверяем результат
        assert len(coins) == 1
        assert coins[0]['id'] == 'bitcoin'
        assert coins[0]['name'] == 'Bitcoin'
        assert coins[0]['symbol'] == 'BTC'
        
        # Проверяем, что был вызван правильный URL
        mock_client_session.get.assert_called_once()
        args, kwargs = mock_client_session.get.call_args
        assert args[0] == 'https://api.cryptorank.io/v1/coins'
        assert kwargs['params']['api_key'] == 'test_api_key'

@pytest.mark.asyncio
async def test_get_coin_details(mock_config, mock_response, mock_session, mock_client_session):
    """Тест получения информации о монете"""
    with patch('crypto.data_sources.cryptorank_api.get_config', return_value=mock_config), \
         patch('crypto.data_sources.cryptorank_api.get_cryptorank_api_key', return_value='test_api_key'), \
         patch('aiohttp.ClientSession', return_value=mock_client_session):
        
        # Настраиваем моки
        mock_client_session.get.return_value = mock_session
        mock_session.status = 200
        mock_session.json = asyncio.coroutine(lambda: {'data': {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC'}})
        
        # Создаем экземпляр API
        api = CryptorankAPI()
        
        # Вызываем метод
        coin = await api.get_coin_details('bitcoin')
        
        # Проверяем результат
        assert coin['id'] == 'bitcoin'
        assert coin['name'] == 'Bitcoin'
        assert coin['symbol'] == 'BTC'
        
        # Проверяем, что был вызван правильный URL
        mock_client_session.get.assert_called_once()
        args, kwargs = mock_client_session.get.call_args
        assert args[0] == 'https://api.cryptorank.io/v1/coins/bitcoin'
        assert kwargs['params']['api_key'] == 'test_api_key'

@pytest.mark.asyncio
async def test_api_error_handling(mock_config, mock_session, mock_client_session):
    """Тест обработки ошибок API"""
    with patch('crypto.data_sources.cryptorank_api.get_config', return_value=mock_config), \
         patch('crypto.data_sources.cryptorank_api.get_cryptorank_api_key', return_value='test_api_key'), \
         patch('aiohttp.ClientSession', return_value=mock_client_session):
        
        # Настраиваем моки для имитации ошибки
        mock_client_session.get.return_value = mock_session
        mock_session.status = 404
        mock_session.text = asyncio.coroutine(lambda: "Not Found")
        
        # Создаем экземпляр API
        api = CryptorankAPI()
        
        # Вызываем метод и проверяем, что он возвращает пустой список при ошибке
        coins = await api.get_coins()
        assert coins == []