import time
import hmac
import hashlib
import requests
from typing import Dict, Optional

from config import MEX_API_KEY, MEX_SECRET_KEY


class FuturesAPI:
    """Минимальный клиент для MEXC Contract API (фьючерсы).

    Делает попытку авторизации через заголовки (ApiKey/Request-Time/Signature).
    При неуспехе пробует query-подпись как fallback.
    """

    def __init__(self, base_url: str = 'https://contract.mexc.com', timeout: int = 10,
                 max_retries: int = 3):
        self.base_url = base_url.rstrip('/')
        self.api_key = MEX_API_KEY
        self.secret_key = MEX_SECRET_KEY
        self.timeout = timeout
        self.max_retries = max_retries

    def _hmac_sha256_hex(self, payload: str) -> str:
        return hmac.new(self.secret_key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

    def _request_with_retries(self, method: str, url: str, **kwargs) -> Dict:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = self.timeout
                resp = requests.request(method=method.upper(), url=url, **kwargs)
                if resp.status_code == 200:
                    return resp.json()
                # вернём тело даже при !=200 — полезно для диагностики
                try:
                    return {'error': f'HTTP {resp.status_code}', 'data': resp.json()}
                except Exception:
                    return {'error': f'HTTP {resp.status_code}', 'text': resp.text}
            except Exception as e:
                last_error = e
                # небольшая линейная задержка
                time.sleep(1 + attempt)
        return {'error': 'request_failed', 'message': str(last_error) if last_error else 'unknown'}

    def _signed_headers(self, method: str, endpoint: str, query: str = '', body: str = '') -> Dict[str, str]:
        req_time = str(int(time.time() * 1000))
        # Подпись: reqTime + method + endpoint + query + body
        sign_payload = f"{req_time}{method.upper()}{endpoint}{query}{body}"
        signature = self._hmac_sha256_hex(sign_payload)
        return {
            'Content-Type': 'application/json',
            'ApiKey': self.api_key,
            'Request-Time': req_time,
            'Signature': signature,
        }

    def get_account_asset(self) -> Dict:
        """Получить активы фьючерсного аккаунта.

        Сначала пробует header-sign, затем fallback на query-sign.
        """
        endpoint = '/api/v1/private/account/assets'
        url = f"{self.base_url}{endpoint}"

        # 1) Попытка с подписью в заголовках
        headers = self._signed_headers('GET', endpoint, '', '')
        result = self._request_with_retries('GET', url, headers=headers)
        # Если пришла явная ошибка авторизации — пробуем query-подпись
        if isinstance(result, dict) and result.get('error'):
            # 2) fallback: query-подпись
            ts = int(time.time() * 1000)
            query = f"timestamp={ts}"
            sig = self._hmac_sha256_hex(query)
            q_url = f"{url}?{query}&signature={sig}"
            q_headers = {'Content-Type': 'application/json', 'X-MEXC-APIKEY': self.api_key}
            return self._request_with_retries('GET', q_url, headers=q_headers)
        return result

    def get_account_info(self) -> Dict:
        """Альтернативный эндпоинт информации аккаунта (если доступен)."""
        endpoint = '/api/v1/account/info'
        url = f"{self.base_url}{endpoint}"
        headers = self._signed_headers('GET', endpoint, '', '')
        result = self._request_with_retries('GET', url, headers=headers)
        if isinstance(result, dict) and result.get('error'):
            ts = int(time.time() * 1000)
            query = f"timestamp={ts}"
            sig = self._hmac_sha256_hex(query)
            q_url = f"{url}?{query}&signature={sig}"
            q_headers = {'Content-Type': 'application/json', 'X-MEXC-APIKEY': self.api_key}
            return self._request_with_retries('GET', q_url, headers=q_headers)
        return result


