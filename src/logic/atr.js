// src/logic/atr.js
"use strict";

/**
 * Расчет ATR (Average True Range) для определения волатильности
 * @param {Array} ohlcvData - Массив данных OHLCV
 * @param {number} period - Период расчета ATR (по умолчанию 14)
 * @returns {number} Значение ATR
 */
function calculateATR(ohlcvData, period = 14) {
  if (!ohlcvData || ohlcvData.length < 2) {
    return 0;
  }
  
  // Расчет True Range для каждого бара
  const trValues = [];
  
  for (let i = 1; i < ohlcvData.length; i++) {
    const current = ohlcvData[i];
    const prev = ohlcvData[i-1];
    
    const tr = Math.max(
      current.high - current.low, // Диапазон текущего бара
      Math.abs(current.high - prev.close), // Разница между максимумом текущего и закрытием предыдущего
      Math.abs(current.low - prev.close) // Разница между минимумом текущего и закрытием предыдущего
    );
    
    trValues.push(tr);
  }
  
  // Расчет ATR
  if (trValues.length <= period) {
    // Простое среднее для первых значений
    const sum = trValues.reduce((acc, val) => acc + val, 0);
    return sum / trValues.length;
  } else {
    // Экспоненциальное скользящее среднее для последующих значений
    let atr = trValues.slice(0, period).reduce((acc, val) => acc + val, 0) / period;
    
    for (let i = period; i < trValues.length; i++) {
      atr = (atr * (period - 1) + trValues[i]) / period;
    }
    
    return atr;
  }
}

module.exports = {
  calculateATR
};