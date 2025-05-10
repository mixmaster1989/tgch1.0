"use strict";

/**
 * Заглушка для получения рейтингов монет с Cryptorank
 * @param {string} symbol - Символ пары (например, "BTC_USDT")
 * @returns {Object} Объект с данными по монете
 */
function getCoinRating(symbol) {
  // В реальной реализации здесь будет запрос к Cryptorank API
  // Для примера возвращаем тестовые данные
  
  // Извлечение символа монеты
  const coin = symbol.split('_')[0].toLowerCase();
  
  return {
    symbol: coin,
    name: {
      'btc': 'Bitcoin',
      'eth': 'Ethereum',
      'sol': 'Solana'
    }[coin] || 'Unknown',
    price: Math.random() * 100000, // Случайная цена
    marketCap: Math.random() * 1e12, // Случайная рыночная капитализация
    volume24h: Math.random() * 1e10, // Случайный объем торгов
    rank: Math.floor(Math.random() * 100) + 1, // Случайный ранг
    category: {
      'btc': 'Биткоин и альткойны',
      'eth': 'Эфириум и альткойны',
      'sol': 'Высокая волатильность',
      default: 'Неизвестно'
    }[coin] || 'Неизвестно',
    updated: new Date().toISOString()
  };
}

/**
 * Получение данных по всем подписанным парам
 * @param {Array} symbols - Массив символов пар (например, ["BTC_USDT", "ETH_USDT"])
 * @returns {Object} Объект с данными по всем монетам
 */
function getMarketData(symbols = ["BTC_USDT", "ETH_USDT"]) {
  return {
    timestamp: new Date().toISOString(),
    data: symbols.reduce((acc, symbol) => {
      acc[symbol] = getCoinRating(symbol);
      return acc;
    }, {})
  };
}

module.exports = {
  getCoinRating,
  getMarketData
};