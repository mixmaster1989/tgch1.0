import sqlite3
import json

def init_db(db_path='profiles.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            settings TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Получить профиль по символу
def get_profile_by_symbol(symbol, db_path='profiles.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT settings FROM profiles WHERE name=?', (symbol,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

# Получить все профили
def get_all_profiles(db_path='profiles.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT name, settings FROM profiles')
    rows = c.fetchall()
    conn.close()
    return [(name, json.loads(settings)) for name, settings in rows]

# Добавить или обновить профиль
def upsert_profile(symbol, settings, db_path='profiles.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT INTO profiles (name, settings) VALUES (?, ?)
                 ON CONFLICT(name) DO UPDATE SET settings=excluded.settings''',
              (symbol, json.dumps(settings)))
    conn.commit()
    conn.close()

# Удалить профиль
def delete_profile(symbol, db_path='profiles.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM profiles WHERE name=?', (symbol,))
    conn.commit()
    conn.close()

# Проверка риск-менеджмента перед открытием ордера
# profile: dict, order_params: dict (например, {'size': 0.1})
def check_risk_management(profile, order_params, stats=None):
    # stats — словарь с текущими торговыми показателями (PnL, количество сделок и т.д.)
    max_position_size = profile.get('max_position_size')
    max_daily_loss = profile.get('max_daily_loss')
    max_trades_per_day = profile.get('max_trades_per_day')
    # Проверка размера позиции
    if max_position_size is not None and order_params.get('size', 0) > max_position_size:
        return False, f"Превышен лимит размера позиции: {order_params.get('size')} > {max_position_size}"
    # Проверка количества сделок
    if max_trades_per_day is not None and stats and stats.get('trades_today', 0) >= max_trades_per_day:
        return False, f"Превышен лимит сделок в день: {stats.get('trades_today')} >= {max_trades_per_day}"
    # Проверка дневного убытка
    if max_daily_loss is not None and stats and stats.get('daily_loss', 0) <= -abs(max_daily_loss):
        return False, f"Превышен лимит дневного убытка: {stats.get('daily_loss')} <= -{max_daily_loss}"
    return True, "Ок"

# Пример структуры профиля:
# {
#   "order_type": "market",
#   "size": 0.01,
#   "leverage": 20,
#   "tp1": 10000,         # Первый тейк-профит
#   "tp2": 11000,         # Второй тейк-профит
#   "sl": 9000,           # Стоп-лосс
#   "trailing": 100,      # Трейлинг-стоп (активируется после TP1)
#   "monitor_interval": 300,
#   "max_position_size": 1.0,
#   "max_daily_loss": 100,
#   "max_trades_per_day": 5
# } 