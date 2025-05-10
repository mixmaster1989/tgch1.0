// src/data/ws-mexc.js
"use strict";

const WebSocket = require('ws');
const EventEmitter = require('events');

/**
 * Клиент для подключения к WebSocket API MEXC
 */
class MEXCWebSocket extends EventEmitter {
  constructor() {
    super();
    this.uri = "wss://wbs.mexc.com/raw";
    this.pairs = ["BTC_USDT", "ETH_USDT"]; // Пары для отслеживания
    this.ohlcv = {}; // Хранение данных OHLCV
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 5000;
    
    this.init();
  }

  /**
   * Инициализация WebSocket подключения
   */
  init() {
    this.ws = new WebSocket(this.uri);

    this.ws.on('open', () => {
      console.log("WebSocket: Подключение установлено");
      this.reconnectAttempts = 0;
      this.subscribeToPairs();
    });

    this.ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        this.processMessage(message);
      } catch (error) {
        console.error("Ошибка обработки сообщения WebSocket:", error);
      }
    });

    this.ws.on('error', (error) => {
      console.error("WebSocket ошибка:", error);
      this.handleReconnect();
    });

    this.ws.on('close', (code, reason) => {
      console.log(`WebSocket закрыт: код ${code}, причина: ${reason}`);
      this.handleReconnect();
    });
  }

  /**
   * Подписка на данные по заданным парам
   */
  subscribeToPairs() {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.pairs.forEach(pair => {
        const subscribeMsg = {
          method: "SUBSCRIBE",
          params: [`${pair.toLowerCase().replace('_', '')}@kline_1m`],
          id: 1
        };
        this.ws.send(JSON.stringify(subscribeMsg));
      });
    }
  }

  /**
   * Обработка входящих сообщений
   * @param {Object} message - Полученное сообщение
   */
  processMessage(message) {
    if (message && message.data && message.data.k) {
      const symbol = message.data.s;
      const kline = message.data.k;
      
      // Извлечение данных свечи
      const candle = {
        timestamp: kline.t,
        open: parseFloat(kline.o),
        high: parseFloat(kline.h),
        low: parseFloat(kline.l),
        close: parseFloat(kline.c),
        volume: parseFloat(kline.v)
      };
      
      // Добавление данных в хранилище
      if (!this.ohlcv[symbol]) {
        this.ohlcv[symbol] = [];
      }
      
      this.ohlcv[symbol].push(candle);
      
      // Ограничение длины хранилища (например, последние 100 свечей)
      if (this.ohlcv[symbol].length > 100) {
        this.ohlcv[symbol] = this.ohlcv[symbol].slice(-100);
      }
      
      // Эмитирование события новой свечи
      this.emit('onNewCandle', symbol, candle);
    }
  }

  /**
   * Получение последних данных OHLCV для заданной пары
   * @param {string} symbol - Символ пары (например, "BTC_USDT")
   * @param {number} limit - Количество свечей (по умолчанию 100)
   * @returns {Array} Массив данных OHLCV
   */
  getOHLCV(symbol, limit = 100) {
    if (!this.ohlcv[symbol]) {
      return [];
    }
    return this.ohlcv[symbol].slice(-limit);
  }

  /**
   * Обработка повторного подключения
   */
  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Попытка повторного подключения ${this.reconnectAttempts}/${this.maxReconnectAttempts} через ${this.reconnectDelay / 1000} секунд...`);
      setTimeout(() => this.init(), this.reconnectDelay);
    } else {
      console.error("Достигнуто максимальное количество попыток подключения");
    }
  }
}

module.exports = MEXCWebSocket;