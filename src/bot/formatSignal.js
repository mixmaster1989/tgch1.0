// src/bot/formatSignal.js
"use strict";

/**
 * Форматирование сигнала в Markdown для отправки в Telegram
 * @param {Object} signal - Объект торгового сигнала
 * @returns {Object} Объект с текстом сигнала и опциями для Telegram
 */
function formatSignal(signal) {
  if (!signal || !signal.pair || !signal.signalType) {
    throw new Error("Некорректные данные сигнала");
  }
  
  // Определение эмодзи в зависимости от типа сигнала
  const signalEmoji = signal.signalType === 'Long' ? "📈" : "📉";
  
  // Формирование текста сигнала
  let message = `${signalEmoji} ${signal.pair} ▸ ${signal.signalType}\\n`;
  message += `🔴 Уверенность: ${(signal.confidence * 100).toFixed(0)}%\\n`;
  message += `💥 Вход: $${signal.entry.toFixed(2)}\\n`;
  message += `🛑 Стоп: $${signal.stop.toFixed(2)}\\n`;
  message += `🎯 TP1: $${signal.tp1.toFixed(2)} | TP2: $${signal.tp2.toFixed(2)}\\n`;
  message += `📊 R:R = ${signal.rrRatio}\\n`;
  message += `⏱ Горизонт: ${signal.horizon}`;
  
  // Формирование опций с кнопкой Cryptorank
  const options = {
    reply_markup: {
      inline_keyboard: [[
        {
          text: '🔍 Cryptorank',
          url: `https://cryptorank.io/price/${signal.pair.replace('_', '').toLowerCase()}`
        }
      ]],
      parse_mode: 'MarkdownV2',
      disable_web_page_preview: true
    }
  };
  
  return {
    text: message,
    options
  };
}

module.exports = { formatSignal };