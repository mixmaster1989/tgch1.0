import requests
import json
import time
from typing import Dict, List, Optional
from config import (
    OPENROUTER_API_KEY, OPENROUTER_SILVER_KEY_1, 
    OPENROUTER_SILVER_KEY_2, OPENROUTER_SILVER_KEY_3,
    GOLDEN_MODEL, SILVER_MODEL
)

class OpenRouterManager:
    def __init__(self):
        # Golden key для торговых решений
        self.golden_key = OPENROUTER_API_KEY
        
        # Silver keys для повседневных задач
        self.silver_keys = [
            key for key in [
                OPENROUTER_SILVER_KEY_1,
                OPENROUTER_SILVER_KEY_2, 
                OPENROUTER_SILVER_KEY_3
            ] if key and key != 'your_openrouter_silver_key_1'
        ]
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.current_silver_index = 0
        self.failed_keys = set()  # Ключи с исчерпанным лимитом
        
    def _make_request(self, api_key: str, prompt: str, model: str = "anthropic/claude-3-haiku") -> Dict:
        """Выполнить запрос к OpenRouter API"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],

            'temperature': 0.3
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            return {
                'status_code': response.status_code,
                'response': response.json() if response.status_code == 200 else response.text,
                'success': response.status_code == 200
            }
            
        except Exception as e:
            return {
                'status_code': 0,
                'response': str(e),
                'success': False
            }
    
    def _is_rate_limit_error(self, result: Dict) -> bool:
        """Проверить, является ли ошибка превышением лимита"""
        if not result['success']:
            error_text = str(result['response']).lower()
            return any(keyword in error_text for keyword in [
                'rate limit', 'daily limit', 'quota exceeded', 
                'too many requests', 'limit exceeded'
            ])
        return False
    
    def _get_next_silver_key(self) -> Optional[str]:
        """Получить следующий доступный silver ключ"""
        attempts = 0
        while attempts < len(self.silver_keys):
            key = self.silver_keys[self.current_silver_index]
            
            # Переходим к следующему ключу
            self.current_silver_index = (self.current_silver_index + 1) % len(self.silver_keys)
            attempts += 1
            
            # Проверяем, не заблокирован ли ключ
            if key not in self.failed_keys:
                return key
                
        return None
    
    def request_with_silver_keys(self, prompt: str, model: str = None) -> Dict:
        """Выполнить запрос с использованием silver ключей с переключением при лимите"""
        attempts = 0
        max_attempts = len(self.silver_keys)
        
        while attempts < max_attempts:
            current_key = self._get_next_silver_key()
            
            if not current_key:
                return {
                    'success': False,
                    'response': 'Все silver ключи исчерпали дневной лимит',
                    'key_used': None
                }
            
            result = self._make_request(current_key, prompt, model or SILVER_MODEL)
            
            if result['success']:
                return {
                    'success': True,
                    'response': result['response']['choices'][0]['message']['content'],
                    'key_used': current_key[:20] + "..."
                }
            
            # Если превышен лимит, добавляем ключ в заблокированные
            if self._is_rate_limit_error(result):
                self.failed_keys.add(current_key)
                print(f"Silver ключ исчерпал лимит, переключаюсь на следующий...")
                attempts += 1
                continue
            else:
                # Другая ошибка, возвращаем её
                return {
                    'success': False,
                    'response': result['response'],
                    'key_used': current_key[:20] + "..."
                }
        
        return {
            'success': False,
            'response': 'Все silver ключи недоступны',
            'key_used': None
        }
    
    def request_with_golden_key(self, prompt: str, model: str = None) -> Dict:
        """Выполнить запрос с использованием golden ключа для торговых решений"""
        result = self._make_request(self.golden_key, prompt, model or GOLDEN_MODEL)
        
        if result['success']:
            return {
                'success': True,
                'response': result['response']['choices'][0]['message']['content'],
                'key_used': 'GOLDEN_KEY'
            }
        else:
            return {
                'success': False,
                'response': result['response'],
                'key_used': 'GOLDEN_KEY'
            }
    
    def reset_failed_keys(self):
        """Сбросить список заблокированных ключей (вызывать раз в день)"""
        self.failed_keys.clear()
        print("Список заблокированных silver ключей сброшен")
    
    def get_status(self) -> Dict:
        """Получить статус всех ключей"""
        return {
            'golden_key_available': bool(self.golden_key),
            'silver_keys_total': len(self.silver_keys),
            'silver_keys_failed': len(self.failed_keys),
            'silver_keys_available': len(self.silver_keys) - len(self.failed_keys),
            'current_silver_index': self.current_silver_index
        }