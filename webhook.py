from flask import Flask, request, jsonify
import logging
from bitget_api import BitgetAPI
from profiles import get_profile_by_symbol, check_risk_management
from config import load_config
from telegram_bot import send_group_message

# Заглушка для статистики (PnL, сделки за день)
def get_stats_for_symbol(symbol):
    # TODO: Реализовать реальную статистику (например, из базы или файла)
    return {
        'trades_today': 0,
        'daily_loss': 0.0
    }

def start_webhook_server(config):
    app = Flask(__name__)
    bitget = BitgetAPI(
        config['BITGET_API_KEY'],
        config['BITGET_API_SECRET'],
        config['BITGET_API_PASSPHRASE']
    )

    @app.route('/webhook', methods=['POST'])
    def webhook():
        data = request.json
        logging.info(f"Получен сигнал: {data}")
        try:
            symbol = data.get('symbol')
            side = data.get('side')
            if not symbol or not side:
                return jsonify({'status': 'error', 'msg': 'symbol/side required'}), 400
            profile = get_profile_by_symbol(symbol, config['DB_PATH'])
            if not profile:
                return jsonify({'status': 'error', 'msg': 'profile not found'}), 404
            # Проверка риск-менеджмента
            stats = get_stats_for_symbol(symbol)
            ok, msg = check_risk_management(profile, data, stats)
            if not ok:
                send_group_message(config, f'❗️Ограничение риска: {msg} (сигнал по {symbol} не исполнен)')
                return jsonify({'status': 'error', 'msg': msg}), 403
            if side.lower() in ['buy', 'long']:
                result = bitget.open_order(symbol, 'buy', profile)
            elif side.lower() in ['sell', 'short']:
                result = bitget.open_order(symbol, 'sell', profile)
            else:
                return jsonify({'status': 'error', 'msg': 'unknown side'}), 400
            if result and result.get('code') == '00000':
                msg = f'✅ Открыт ордер {side} по {symbol} через webhook.'
                send_group_message(config, msg)
                return jsonify({'status': 'ok'})
            else:
                err = result.get('msg', 'Неизвестная ошибка') if result else 'Нет ответа от API'
                send_group_message(config, f'❗️Ошибка открытия ордера по {symbol}: {err}')
                return jsonify({'status': 'error', 'msg': err}), 500
        except Exception as e:
            logging.error(f"Ошибка обработки сигнала: {e}")
            send_group_message(config, f'❗️Ошибка открытия ордера по {symbol}: {e}')
            return jsonify({'status': 'error', 'msg': str(e)}), 500

    app.run(host='0.0.0.0', port=config['WEBHOOK_PORT']) 