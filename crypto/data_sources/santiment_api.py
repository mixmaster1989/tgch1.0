import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.santiment_api')

class SantimentAPI:
    """
    Класс для работы с API Santiment
    """
    
    def __init__(self, api_key: str):
        """
        Инициализирует Santiment API клиент
        
        Args:
            api_key: API-ключ для аутентификации
        """
        self.api_key = api_key
        self.base_url = "https://api.santiment.net/graphql"
        self.headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        }
        
        logger.info("Инициализирован клиент Santiment API")

    def _make_request(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Выполняет GraphQL-запрос к API Santiment
        
        Args:
            query: GraphQL-запрос
            
        Returns:
            Optional[Dict[str, Any]]: Результат запроса или None в случае ошибки
        """
        try:
            logger.debug(f"Выполнение GraphQL-запроса: {query}")
            
            response = requests.post(
                self.base_url,
                json={"query": query},
                headers=self.headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                logger.error(f"Ошибки в ответе от Santiment API: {result['errors']}")
                return None
            
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса к Santiment API: {e}")
            return None
    
    def get_project_metrics(self, slug: str, metric: str, from_date: datetime, to_date: datetime) -> Optional[List[Dict[str, Any]]]:
        """
        Получает метрики проекта за определенный период
        
        Args:
            slug: Идентификатор проекта (например, "bitcoin")
            metric: Название метрики (например, "dev_activity")
            from_date: Дата начала периода
            to_date: Дата окончания периода
            
        Returns:
            Optional[List[Dict[str, Any]]]: Список метрик за период или None
        """
        # Формируем даты в формате ISO
        from_iso = from_date.isoformat()
        to_iso = to_date.isoformat()
        
        # GraphQL-запрос
        query = f"""
        {{
          getMetric(metric: "{metric}") {{
            timeseriesData(slug: "{slug}", from: "{from_iso}", to: "{to_iso}", interval: "1d") {{
              timestamp
              value
            }}
          }}
        }}
        """
        
        result = self._make_request(query)
        
        if not result:
            return None
        
        # Извлекаем данные
        data = result.get("getMetric", {}).get("timeseriesData", [])
        
        # Преобразуем timestamp из строки в datetime
        for item in data:
            if isinstance(item["timestamp"], str):
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
        
        return data
    
    def get_dev_activity(self, slug: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Получает данные о разработке проекта за последние N дней
        
        Args:
            slug: Идентификатор проекта (например, "bitcoin")
            days: Количество дней истории
            
        Returns:
            Optional[List[Dict[str, Any]]]: Данные о разработке или None
        """
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        return self.get_project_metrics(slug, "dev_activity", from_date, to_date)
    
    def get_social_volume(self, slug: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Получает данные о социальном объеме проекта за последние N дней
        
        Args:
            slug: Идентификатор проекта (например, "bitcoin")
            days: Количество дней истории
            
        Returns:
            Optional[List[Dict[str, Any]]]: Данные о социальном объеме или None
        """
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        return self.get_project_metrics(slug, "social_volume", from_date, to_date)
    
    def get_exchange_flows(self, slug: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Получает данные о потоках на биржах за последние N дней
        
        Args:
            slug: Идентификатор проекта (например, "bitcoin")
            days: Количество дней истории
            
        Returns:
            Optional[List[Dict[str, Any]]]: Данные о потоках на биржах или None
        """
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        return self.get_project_metrics(slug, "exchange_flows", from_date, to_date)
    
    def get_network_growth(self, slug: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Получает данные о росте сети за последние N дней
        
        Args:
            slug: Идентификатор проекта (например, "bitcoin")
            days: Количество дней истории
            
        Returns:
            Optional[List[Dict[str, Any]]]: Данные о росте сети или None
        """
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        return self.get_project_metrics(slug, "network_growth", from_date, to_date)