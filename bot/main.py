import config
import handlers  # noqa
from aiogram.utils import executor

if __name__ == '__main__':
    executor.start_polling(config.dp, skip_updates=True)
