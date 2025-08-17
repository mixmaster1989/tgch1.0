#!/usr/bin/env python3
"""
Утилиты для работы с балансом USDT и USDC
"""

from typing import Dict, Optional, Tuple
from mex_api import MexAPI
import logging

logger = logging.getLogger(__name__)

def get_usdt_usdc_balance() -> Tuple[float, float]:
    """
    Получить текущий баланс USDT и USDC
    
    Returns:
        Tuple[float, float]: (usdt_balance, usdc_balance)
    """
    try:
        api = MexAPI()
        account_info = api.get_account_info()
        
        if 'error' in account_info or ('code' in account_info and account_info['code'] != 200):
            logger.error(f"Ошибка API: {account_info}")
            return 0.0, 0.0
        
        usdt_balance = 0.0
        usdc_balance = 0.0
        
        for balance in account_info.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if asset == 'USDT':
                usdt_balance = total
            elif asset == 'USDC':
                usdc_balance = total
        
        logger.info(f"Баланс получен: USDT={usdt_balance:.8f}, USDC={usdc_balance:.8f}")
        return usdt_balance, usdc_balance
        
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        return 0.0, 0.0

def get_balance_dict() -> Dict[str, float]:
    """
    Получить баланс USDT и USDC в виде словаря
    
    Returns:
        Dict[str, float]: {'usdt': balance, 'usdc': balance}
    """
    usdt, usdc = get_usdt_usdc_balance()
    return {
        'usdt': usdt,
        'usdc': usdc,
        'total': usdt + usdc
    }

def get_free_balance() -> Tuple[float, float]:
    """
    Получить только свободный баланс USDT и USDC (без заблокированных средств)
    
    Returns:
        Tuple[float, float]: (free_usdt, free_usdc)
    """
    try:
        api = MexAPI()
        account_info = api.get_account_info()
        
        if 'error' in account_info or ('code' in account_info and account_info['code'] != 200):
            logger.error(f"Ошибка API: {account_info}")
            return 0.0, 0.0
        
        free_usdt = 0.0
        free_usdc = 0.0
        
        for balance in account_info.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            
            if asset == 'USDT':
                free_usdt = free
            elif asset == 'USDC':
                free_usdc = free
        
        logger.info(f"Свободный баланс: USDT={free_usdt:.8f}, USDC={free_usdc:.8f}")
        return free_usdt, free_usdc
        
    except Exception as e:
        logger.error(f"Ошибка получения свободного баланса: {e}")
        return 0.0, 0.0

def check_balance_sufficient(required_usdt: float = 0.0, required_usdc: float = 0.0) -> bool:
    """
    Проверить, достаточно ли баланса для операций
    
    Args:
        required_usdt: Требуемый баланс USDT
        required_usdc: Требуемый баланс USDC
    
    Returns:
        bool: True если баланса достаточно
    """
    free_usdt, free_usdc = get_free_balance()
    
    if free_usdt < required_usdt:
        logger.warning(f"Недостаточно USDT: требуется {required_usdt}, доступно {free_usdt}")
        return False
    
    if free_usdc < required_usdc:
        logger.warning(f"Недостаточно USDC: требуется {required_usdc}, доступно {free_usdc}")
        return False
    
    return True 