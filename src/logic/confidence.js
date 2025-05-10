// src/logic/confidence.js
"use strict";

/**
 * Расчет уровня уверенности в торговом сигнале
 * @param {Array} ohlcvData - Массив данных OHLCV
 * @param {Object} config - Конфигурационные данные
 * @returns {number} Уровень уверенности от 0 до 1
 */
function calculateConfidence(ohlcvData, config = {}) {
  // Проверка входных данных
  if (!ohlcvData || ohlcvData.length < 10) {
    console.warn("Недостаточно данных для расчета уверенности");
    return 0.5; // Возвращаем среднее значение при недостатке данных
  }
  
  // Получение параметров из конфигурации или установка значений по умолчанию
  const weights = {
    volume: 0.4,
    rsi: 0.3,
    density: 0.3,
    ...config.confidenceWeights
  };
  
  // Расчет факторов
  const factors = {
    volume: calculateVolumeFactor(ohlcvData, config),
    rsi: calculateRsiFactor(ohlcvData, config),
    density: calculateDensityFactor(ohlcvData, config)
  };
  
  // Расчет итоговой уверенности
  let confidence = (
    factors.volume * weights.volume +
    factors.rsi * weights.rsi +
    factors.density * weights.density
  ).toFixed(2);
  
  // Ограничение уверенности в диапазоне 0.3-0.8
  confidence = Math.max(0.3, Math.min(0.8, parseFloat(confidence)));
  
  return confidence;
}

/**
 * Расчет фактора объема на основе волатильности
 * @param {Array} ohlcvData - Массив данных OHLCV
 * @param {Object} config - Конфигурационные данные
 * @returns {number} Фактор объема от 0 до 1
 */
function calculateVolumeFactor(ohlcvData, config = {}) {
  // Пример простого расчета на основе волатильности
  const latest = ohlcvData[ohlcvData.length - 1];
  const prev = ohlcvData[ohlcvData.length - 2] || latest;
  
  // Расчет волатильности
  const volatility = (latest.high - latest.low) / latest.close;
  
  // Нормализация волатильности в фактор объема
  const normalizedVolatility = Math.min(0.8, volatility * 5);
  
  return normalizedVolatility;
}

/**
 * Расчет фактора RSI на основе последних свечей
 * @param {Array} ohlcvData - Массив данных OHLCV
 * @param {Object} config - Конфигурационные данные
 * @returns {number} Фактор RSI от 0 до 1
 */
function calculateRsiFactor(ohlcvData, config = {}) {
  // Проверка входных данных
  if (!ohlcvData || ohlcvData.length < 14) {
    return 0.5; // Среднее значение при недостатке данных
  }
  
  // Расчет RSI
  const period = config.atr ? config.atr.period : 14;
  const recentCandles = ohlcvData.slice(-period);
  
  // Расчет прибыли и потерь
  let gains = 0;
  let losses = 0;
  
  for (let i = 1; i < recentCandles.length; i++) {
    const change = recentCandles[i].close - recentCandles[i-1].close;
    if (change > 0) {
      gains += change;
    } else {
      losses += Math.abs(change);
    }
  }
  
  // Расчет RSI
  const avgGain = gains / period;
  const avgLoss = losses / period;
  
  if (avgGain + avgLoss === 0) {
    return 0.5; // Нейтральное значение при отсутствии изменений
  }
  
  // Расчет RSI
  const rs = avgGain / avgLoss;
  const rsi = 1 - (1 / (1 + rs));
  
  // Нормализация RSI в диапазоне 0-1
  return Math.min(0.9, Math.max(0.1, rsi));
}

/**
 * Расчет фактора плотности на основе кластерного анализа
 * @param {Array} ohlcvData - Массив данных OHLCV
 * @param {Object} config - Конфигурационные данные
 * @returns {number} Фактор плотности от 0 до 1
 */
function calculateDensityFactor(ohlcvData, config = {}) {
  // Пример простого расчета на основе волатильности
  if (!ohlcvData || ohlcvData.length < 5) {
    return 0.5; // Среднее значение при недостатке данных
  }
  
  // Расчет волатильности на основе последних свечей
  const recentCandles = ohlcvData.slice(-5);
  const avgVolatility = recentCandles.reduce((sum, candle, i, arr) => {
    if (i === 0) return sum;
    return sum + (candle.high - candle.low) / candle.close;
  }, 0) / (recentCandles.length - 1);
  
  // Нормализация волатильности в фактор плотности
  const densityFactor = Math.max(0.2, 1 - avgVolatility);
  
  return densityFactor;
}

module.exports = {
  calculateConfidence
};