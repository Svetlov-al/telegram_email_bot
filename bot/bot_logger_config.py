import logging
from logging.handlers import TimedRotatingFileHandler

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Логирование в файл с ротацией каждый день
file_handler = TimedRotatingFileHandler('bot.log', when='midnight', interval=1, backupCount=7)
file_handler.setFormatter(formatter)
file_handler.suffix = '%d-%m-%Y'

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger('my_app_logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
