import logging
import os

def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    ) 