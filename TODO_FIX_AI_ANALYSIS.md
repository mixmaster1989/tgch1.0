# TODO: Исправление проблем AI анализа

## 🚨 Критические ошибки:

### 1. **PerplexityAnalyzer метод не найден**
- **Проблема**: `'PerplexityAnalyzer' object has no attribute 'collect_coin_data'`
- **Решение**: В comprehensive_data_manager заменить `collect_coin_data` на `get_comprehensive_analysis`

### 2. **Session is closed**
- **Проблема**: `Ошибка загрузки рыночных данных для ETHUSDT: Session is closed`
- **Решение**: Проверить управление сессиями в comprehensive_data_manager

### 3. **Correlation analyzer спам**
- **Проблема**: `cannot reindex on an axis with duplicate labels`
- **Решение**: Исправить дублирующиеся метки в pandas DataFrame

## ✅ Что работает:
- WebSocket подключение к MEXC
- Получение ордербука данных
- Загрузка исторических данных
- Perplexity анализ (в тесте)

## 🎯 Цель:
Получить полный AI анализ с реальными данными от comprehensive_data_manager и perplexity_analyzer
