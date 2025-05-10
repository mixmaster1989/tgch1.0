class SignalFormatter:
    def format_signal(self, signal: dict) -> str:
        """
        Форматирование сигнала в Markdown для отправки в Telegram
        """
        # Определение эмодзи в зависимости от типа сигнала
        signal_emoji = "📈" if signal['signal_type'] == 'Long' else "📉"
        
        # Формирование сообщения
        message = f"{signal_emoji} {signal['pair']} ▸ {signal['signal_type']}\n"
        message += f"🟢 Уверенность: {signal['confidence'] * 100:.0f}%\n"
        message += f"🎯 Вход: ${signal['entry']:.2f}\n"
        message += f"🛑 Стоп: ${signal['stop']:.2f}\n"
        message += f"🎯 TP1: ${signal['tp1']:.2f} | TP2: ${signal['tp2']:.2f}\n"
        message += f"📊 R:R = {signal['rr_ratio']:.1f}\n"
        message += f"⏱ Горизонт: {signal['horizon']}"
        
        return message