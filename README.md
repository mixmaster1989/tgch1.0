# Smart Money Signal Bot

Telegram-бот для генерации сигналов на вход в сделку по логике Smart Money, кластерному анализу и волатильности, без графиков и лишнего — чисто в текстовом виде через Telegram.

## 📊 Пример сигнала

```
📈 ETH/USDT ▸ Short  
🔴 Уверенность: 82%  
💥 Вход: $3,124  
🛑 Стоп: $3,180  
🎯 TP1: $3,020 | TP2: $2,950  
📊 R:R = 2.3  
⏱ Горизонт: ~4ч  
```

С кнопкой:
```js
{
  reply_markup: {
    inline_keyboard: [[
      { text: '🔍 Cryptorank', url: `https://cryptorank.io/price/${symbol}` }
    ]]
  }
}
```

## 🧩 Конфигурация (thresholds.json)

```json
{
  "dbscan": {
    "eps": 0.002,
    "minPoints": 3
  },
  "atr": {
    "period": 14,
    "tp1": 1.5,
    "tp2": 3.0,
    "stopLoss": 1.0
  },
  "confidenceWeights": {
    "volume": 0.4,
    "rsi": 0.3,
    "density": 0.3
  }
}
```

## 📦 Структура проекта

```
smart-money-bot/
├── src/
│   ├── data/
│   │   ├── ws-mexc.js              # WebSocket клиент MEXC
│   │   └── cryptorank.js          # Подтяжка рейтингов монет
│   │
│   ├── logic/
│   │   ├── smartMoney.js          # Кластеры, сигналы
│   │   ├── atr.js                 # Волатильность и стопы
│   │   └── confidence.js          # Оценка уверенности
│   │
│   ├── bot/
│   │   ├── telegram.js            # Инициализация бота
│   │   └── formatSignal.js        # Форматирование сигнала
│   │
│   └── config/
│       └── thresholds.json        # Настройки DBSCAN, ATR, веса confidence
│
├── .env                          # API токен Telegram и др.
├── package.json
└── index.js                      # Точка входа
```

## ✅ Установка

1. Скопируйте .env:
```bash
cp .env.example .env
```

2. Отредактируйте .env и внесите свои данные:
```bash
nano .env
```

3. Установите зависимости:
```bash
npm install
```

4. Запустите бота:
```bash
npm start
```

## 🚀 Что вы получаете

Telegram-бот без графиков, но с настоящими сигнальными сообщениями.
Все на Node.js, готово к деплою в любой Docker/VPS.

Одна кнопка: Cryptorank.