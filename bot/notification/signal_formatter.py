from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from .tradingview_link import generate_tv_url

def format_signal(signal):
    """Форматирует сигнал в красивое сообщение с разметкой MarkdownV2"""
    escaped_pair = escape_markdown(signal['pair'])
    return (
        f"📈 *{escaped_pair}* ▸ {signal['direction'].capitalize()}\n"
        f"🟢 Уверенность: `{signal['confidence']}%`\n"
        f"🎯 Вход: `${signal['entry']:.2f}`\n"
        f"🛑 Стоп: `${signal['stop']:.2f}`\n"
        f"🎯 TP1: `${signal['tp1']:.2f}` | TP2: `${signal['tp2']:.2f}`\n"
        f"📊 R:R = `{signal['rr_ratio']:.1f}`\n"
        f"⏱ Горизонт: `{signal['time_horizon']}`"
    )

def get_keyboard(signal):
    """Создает клавиатуру с кнопками для сигнала"""
    return InlineKeyboardMarkup().row(
        InlineKeyboardButton(
            text="📊 TradingView",
            url=generate_tv_url(signal)
        ),
        InlineKeyboardButton(
            text="🔍 Cryptorank",
            callback_data=f"cr_{signal['pair']}"
        )
    )

def escape_markdown(text):
    """Экранирует специальные символы MarkdownV2"""
    escape_chars = r'_[]()~>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in str(text))