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
        key_preview = api_key[:20] + "..." if api_key else "None"
        print(f"🔑 OpenRouter запрос: ключ={key_preview}, модель={model}, промпт={len(prompt)} символов")
        
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
            start_time = time.time()
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            duration = time.time() - start_time
            
            print(f"📡 OpenRouter ответ: статус={response.status_code}, время={duration:.2f}с")
            
            if response.status_code != 200:
                print(f"❌ OpenRouter ошибка: {response.text[:200]}...")
            
            return {
                'status_code': response.status_code,
                'response': response.json() if response.status_code == 200 else response.text,
                'success': response.status_code == 200
            }
            
        except Exception as e:
            print(f"💥 OpenRouter исключение: {str(e)[:200]}...")
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
    
    def _is_key_error(self, result: Dict) -> bool:
        """Проверить, является ли ошибка проблемой с ключом (401, 403, etc)"""
        if not result['success']:
            error_text = str(result['response']).lower()
            return any(keyword in error_text for keyword in [
                'user not found', 'unauthorized', 'forbidden', 'invalid key',
                'authentication failed', 'api key', '401', '403'
            ])
        return False
    
    def _get_next_silver_key(self) -> Optional[str]:
        """Получить следующий доступный silver ключ"""
        print(f"🔄 Поиск доступного silver ключа: индекс={self.current_silver_index}, заблокировано={len(self.failed_keys)}/{len(self.silver_keys)}")
        
        attempts = 0
        while attempts < len(self.silver_keys):
            key = self.silver_keys[self.current_silver_index]
            key_preview = key[:20] + "..." if key else "None"
            
            # Переходим к следующему ключу
            self.current_silver_index = (self.current_silver_index + 1) % len(self.silver_keys)
            attempts += 1
            
            # Проверяем, не заблокирован ли ключ
            if key not in self.failed_keys:
                print(f"✅ Выбран silver ключ: {key_preview}")
                return key
            else:
                print(f"❌ Ключ заблокирован: {key_preview}")
                
        print(f"💀 Все silver ключи заблокированы!")
        return None
    
    def request_with_silver_keys(self, prompt: str, model: str = None) -> Dict:
        """Выполнить запрос с использованием silver ключей с переключением при лимите"""
        print(f"🚀 Запрос с silver ключами: модель={model or SILVER_MODEL}, попыток={len(self.silver_keys) * 3}")
        
        # Пробуем каждый ключ до 3 раз с паузами
        for key_index in range(len(self.silver_keys)):
            for retry in range(3):  # 3 попытки на каждый ключ
                current_key = self.silver_keys[key_index]
                
                if current_key in self.failed_keys:
                    print(f"❌ Ключ {key_index + 1} заблокирован, пропускаю...")
                    break
                
                key_preview = current_key[:20] + "..." if current_key else "None"
                print(f"🔄 Попытка {retry + 1}/3 для ключа {key_index + 1}: {key_preview}")
                
                result = self._make_request(current_key, prompt, model or SILVER_MODEL)
                
                if result['success']:
                    response_text = result['response']['choices'][0]['message']['content']
                    print(f"✅ Silver запрос успешен: ключ {key_index + 1}, ответ {len(response_text)} символов")
                    return {
                        'success': True,
                        'response': response_text,
                        'key_used': current_key[:20] + "..."
                    }
                
                # Если превышен лимит или проблема с ключом
                if self._is_rate_limit_error(result) or self._is_key_error(result):
                    error_type = "исчерпал лимит" if self._is_rate_limit_error(result) else "проблема с ключом"
                    print(f"⚠️ Ключ {key_index + 1} {error_type}, попытка {retry + 1}/3")
                    
                    if retry < 2:  # Если это не последняя попытка для этого ключа
                        wait_time = 1 + retry  # 1, 2, 3 секунды
                        print(f"⏳ Ждем {wait_time} сек перед следующей попыткой...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Последняя попытка для этого ключа, блокируем его
                        self.failed_keys.add(current_key)
                        print(f"💀 Ключ {key_index + 1} заблокирован после 3 попыток")
                        break
                else:
                    # Другая ошибка, пробуем следующий ключ
                    print(f"❌ Ключ {key_index + 1} вернул ошибку: {str(result['response'])[:100]}...")
                    break
        
        print(f"💀 Все silver ключи недоступны после {len(self.silver_keys) * 3} попыток")
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