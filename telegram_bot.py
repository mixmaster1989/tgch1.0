from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from bitget_api import BitgetAPI
from profiles import (
    get_profile_by_symbol, get_all_profiles, upsert_profile, delete_profile
)
from config import load_config
import threading
import time
import json

bot_instance = None

DEFAULT_MONITOR_INTERVAL = 300  # по умолчанию 5 минут
monitored_symbols = set()
monitored_symbols_lock = threading.Lock()

# Шаблоны уведомлений (можно расширять и настраивать)
NOTIFY_TEMPLATES = {
    'order_opened': '✅ Открыт ордер {side} по {symbol} (размер: {size})',
    'order_error': '❗️Ошибка открытия ордера по {symbol}: {error}',
    'risk_limit': '❗️Ограничение риска: {msg} (сигнал по {symbol} не исполнен)',
    'order_partial': '⚠️ Частичное исполнение ордера по {symbol}: исполнено {filled}/{size}',
    'balance_change': '💰 Баланс изменён: {coin} {old} → {new}',
}

def send_group_message(config, text):
    global bot_instance
    if not bot_instance:
        bot_instance = Bot(token=config['TELEGRAM_TOKEN'])
    bot_instance.send_message(chat_id=config['TELEGRAM_GROUP_ID'], text=text)

def monitor_position_for_symbol(config, bitget, symbol):
    profile = get_profile_by_symbol(symbol, config['DB_PATH'])
    interval = profile.get('monitor_interval', DEFAULT_MONITOR_INTERVAL) if profile else DEFAULT_MONITOR_INTERVAL
    tp1 = profile.get('tp1')
    tp2 = profile.get('tp2')
    sl = profile.get('sl')
    trailing = profile.get('trailing')
    tp1_close_percent = profile.get('tp1_close_percent', 50)
    trailing_active = False
    trailing_level = None
    tp1_hit = False
    side = None
    entry_price = None
    while True:
        try:
            positions = bitget.get_positions()
            pos = next((p for p in positions if p.get('symbol') == symbol), None)
            if not pos:
                send_group_message(config, f'Позиция по {symbol} закрыта, мониторинг остановлен.')
                break
            size = float(pos.get('total', 0))
            side = pos.get('holdSide', '-')
            pnl = pos.get('unrealizedPL', '-')
            mark_price = float(pos.get('marketPrice', 0))
            if not entry_price:
                entry_price = float(pos.get('openPrice', mark_price))
            # TP1
            if tp1 and not tp1_hit:
                if (side == 'long' and mark_price >= tp1) or (side == 'short' and mark_price <= tp1):
                    tp1_hit = True
                    # Закрываем часть позиции
                    close_size = round(size * tp1_close_percent / 100, 6)
                    if close_size > 0:
                        bitget.close_order(symbol, side, size=close_size)
                        send_group_message(config, f'🎯 TP1 по {symbol} достигнут ({mark_price}). Зафиксировано {tp1_close_percent}% позиции ({close_size}). Включён трейлинг-стоп.')
                    else:
                        send_group_message(config, f'🎯 TP1 по {symbol} достигнут ({mark_price}). Размер позиции слишком мал для частичного закрытия.')
                    if trailing:
                        trailing_active = True
                        trailing_level = mark_price - trailing if side == 'long' else mark_price + trailing
            # Trailing
            if trailing_active and trailing:
                if side == 'long':
                    if mark_price - trailing > trailing_level:
                        trailing_level = mark_price - trailing
                    if mark_price <= trailing_level:
                        bitget.close_order(symbol, side)
                        send_group_message(config, f'🚨 Трейлинг-стоп по {symbol} сработал ({mark_price}). Позиция закрыта.')
                        break
                    if tp2 and mark_price >= tp2:
                        bitget.close_order(symbol, side)
                        send_group_message(config, f'🏁 TP2 по {symbol} достигнут ({mark_price}). Позиция закрыта.')
                        break
                elif side == 'short':
                    if mark_price + trailing < trailing_level:
                        trailing_level = mark_price + trailing
                    if mark_price >= trailing_level:
                        bitget.close_order(symbol, side)
                        send_group_message(config, f'🚨 Трейлинг-стоп по {symbol} сработал ({mark_price}). Позиция закрыта.')
                        break
                    if tp2 and mark_price <= tp2:
                        bitget.close_order(symbol, side)
                        send_group_message(config, f'🏁 TP2 по {symbol} достигнут ({mark_price}). Позиция закрыта.')
                        break
            # SL
            if sl:
                if (side == 'long' and mark_price <= sl) or (side == 'short' and mark_price >= sl):
                    bitget.close_order(symbol, side)
                    send_group_message(config, f'🛑 SL по {symbol} сработал ({mark_price}). Позиция закрыта.')
                    break
            # Обычный мониторинг
            text = f'Мониторинг {symbol}: {side} {size} PnL: {pnl} Цена: {mark_price}'
            send_group_message(config, text)
        except Exception as e:
            logging.error(f'Ошибка мониторинга {symbol}: {e}')
        time.sleep(interval)
    with monitored_symbols_lock:
        monitored_symbols.discard(symbol)

def monitor_new_positions_loop(config, bitget):
    while True:
        try:
            positions = bitget.get_positions()
            symbols = set(p.get('symbol') for p in positions if p.get('symbol'))
            with monitored_symbols_lock:
                new_symbols = symbols - monitored_symbols
                for symbol in new_symbols:
                    t = threading.Thread(target=monitor_position_for_symbol, args=(config, bitget, symbol), daemon=True)
                    t.start()
                    monitored_symbols.add(symbol)
        except Exception as e:
            logging.error(f'Ошибка автостарта мониторинга: {e}')
        time.sleep(60)  # Проверять раз в минуту

def start_telegram_bot(config):
    global bot_instance
    bot_instance = Bot(token=config['TELEGRAM_TOKEN'])
    updater = Updater(token=config['TELEGRAM_TOKEN'], use_context=True)
    dispatcher = updater.dispatcher
    bitget = BitgetAPI(
        config['BITGET_API_KEY'],
        config['BITGET_API_SECRET'],
        config['BITGET_API_PASSPHRASE']
    )

    # Запуск автостарта мониторинга новых позиций
    monitor_new_thread = threading.Thread(target=monitor_new_positions_loop, args=(config, bitget), daemon=True)
    monitor_new_thread.start()

    def start(update: Update, context: CallbackContext):
        update.message.reply_text('Бот автотрейдера Bitget запущен!')

    def status(update: Update, context: CallbackContext):
        positions = bitget.get_positions()
        balance = bitget.get_balance()
        text = 'Открытые позиции:\n'
        for pos in positions:
            symbol = pos.get('symbol', '-')
            size = pos.get('total', '-')
            side = pos.get('holdSide', '-')
            text += f"{symbol} {side} {size}\n"
        text += '\nБаланс:\n'
        for acc in balance:
            coin = acc.get('marginCoin', '-')
            avail = acc.get('available', '-')
            text += f"{coin}: {avail}\n"
        update.message.reply_text(text)

    def close(update: Update, context: CallbackContext):
        if len(context.args) < 1:
            update.message.reply_text('Использование: /close <монета> [long|short]')
            return
        symbol = context.args[0]
        side = 'all'
        if len(context.args) > 1:
            arg_side = context.args[1].lower()
            if arg_side in ['long', 'buy']:
                side = 'open_long'
            elif arg_side in ['short', 'sell']:
                side = 'open_short'
        try:
            result = bitget.close_order(symbol, side)
            if result and result.get('code') == '00000':
                msg = f'Позиция по {symbol} ({side}) закрыта.'
                update.message.reply_text(msg)
                send_group_message(config, msg)
            else:
                err = result.get('msg', 'Неизвестная ошибка') if result else 'Нет ответа от API'
                update.message.reply_text(f'Ошибка закрытия: {err}')
                send_group_message(config, f'Ошибка закрытия позиции по {symbol}: {err}')
        except Exception as e:
            update.message.reply_text(f'Ошибка: {e}')
            send_group_message(config, f'Ошибка закрытия позиции по {symbol}: {e}')

    def profiles_cmd(update: Update, context: CallbackContext):
        profiles = get_all_profiles(config['DB_PATH'])
        if not profiles:
            update.message.reply_text('Профили не найдены.')
            return
        text = 'Профили:\n'
        for name, prof in profiles:
            text += f'- {name}\n'
        update.message.reply_text(text)

    def profile_cmd(update: Update, context: CallbackContext):
        if len(context.args) < 1:
            update.message.reply_text('Использование: /profile <symbol>')
            return
        symbol = context.args[0]
        profile = get_profile_by_symbol(symbol, config['DB_PATH'])
        if profile:
            update.message.reply_text(f'Профиль для {symbol}:\n{json.dumps(profile, ensure_ascii=False, indent=2)}')
        else:
            update.message.reply_text(f'Профиль для {symbol} не найден')

    def addprofile_cmd(update: Update, context: CallbackContext):
        if len(context.args) < 2:
            update.message.reply_text('Использование: /addprofile <symbol> <json>')
            return
        symbol = context.args[0]
        try:
            settings = json.loads(' '.join(context.args[1:]))
            upsert_profile(symbol, settings, config['DB_PATH'])
            update.message.reply_text(f'Профиль для {symbol} добавлен/обновлён.')
        except Exception as e:
            update.message.reply_text(f'Ошибка: {e}')

    def editprofile_cmd(update: Update, context: CallbackContext):
        if len(context.args) < 2:
            update.message.reply_text('Использование: /editprofile <symbol> <json>')
            return
        symbol = context.args[0]
        try:
            settings = json.loads(' '.join(context.args[1:]))
            upsert_profile(symbol, settings, config['DB_PATH'])
            update.message.reply_text(f'Профиль для {symbol} обновлён.')
        except Exception as e:
            update.message.reply_text(f'Ошибка: {e}')

    def delprofile_cmd(update: Update, context: CallbackContext):
        if len(context.args) < 1:
            update.message.reply_text('Использование: /delprofile <symbol>')
            return
        symbol = context.args[0]
        delete_profile(symbol, config['DB_PATH'])
        update.message.reply_text(f'Профиль для {symbol} удалён.')

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('close', close))
    dispatcher.add_handler(CommandHandler('profiles', profiles_cmd))
    dispatcher.add_handler(CommandHandler('profile', profile_cmd))
    dispatcher.add_handler(CommandHandler('addprofile', addprofile_cmd))
    dispatcher.add_handler(CommandHandler('editprofile', editprofile_cmd))
    dispatcher.add_handler(CommandHandler('delprofile', delprofile_cmd))

    logging.info('Telegram-бот запущен')
    updater.start_polling()
    updater.idle()

# Пример использования шаблонов:
def notify_order_opened(config, symbol, side, size):
    msg = NOTIFY_TEMPLATES['order_opened'].format(symbol=symbol, side=side, size=size)
    send_group_message(config, msg)

def notify_order_error(config, symbol, error):
    msg = NOTIFY_TEMPLATES['order_error'].format(symbol=symbol, error=error)
    send_group_message(config, msg)

def notify_risk_limit(config, symbol, msg_text):
    msg = NOTIFY_TEMPLATES['risk_limit'].format(symbol=symbol, msg=msg_text)
    send_group_message(config, msg)

def notify_order_partial(config, symbol, filled, size):
    msg = NOTIFY_TEMPLATES['order_partial'].format(symbol=symbol, filled=filled, size=size)
    send_group_message(config, msg)

def notify_balance_change(config, coin, old, new):
    msg = NOTIFY_TEMPLATES['balance_change'].format(coin=coin, old=old, new=new)
    send_group_message(config, msg) 