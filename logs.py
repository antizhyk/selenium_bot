import colorlog
from datetime import datetime
import logging
import hashlib


class LoggerWithEmit:
    def __init__(self, logger, account_id, ):
        """
        Инициализация класса для логирования и отправки сообщений через Socket.IO.

        Args:
            logger (logging.Logger): Экземпляр логгера для записи сообщений.
            account_id (str): Идентификатор аккаунта для определения комнаты.
        """
        self.logger = logger
        self.account_id = account_id

    def log(self, message, level='info'):
        """
        Логирование сообщения с использованием предоставленного логгера и отправка через Socket.IO.

        Args:
            message (str): Сообщение лога.
            level (str): Уровень логирования ('debug', 'info', 'warning', 'error', 'critical').
        """
        # Получаем текущее время
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        # Формируем сообщение с временной меткой
        # full_message = f"{current_time} | {level.upper()}: {message}"
        # Логирование с использованием предоставленного логгера
        if self.logger:
            getattr(self.logger, level)(message)

        # Отправка через Socket.IO
        # room = self.account_id
        # self.socketio.emit(f'log_{room}', {'data': full_message})

        # Сохранение лога в Redis
        # log_key = f'logs:{self.account_id}'
        # self.redis_client.rpush(log_key, full_message)
        # # Ограничение размера хранилища логов для каждого аккаунта, например, последние 1000 сообщений
        # self.redis_client.ltrim(log_key, -1000, -1)


def setup_logging(account_id):
    # Список доступных цветов для логов
    available_colors = ['green', 'cyan', 'magenta', 'yellow', 'blue', 'red']

    # Хешируем account_id, чтобы получить уникальный цвет для каждого аккаунта
    color_index = int(hashlib.md5(str(account_id).encode()).hexdigest(), 16) % len(available_colors)
    account_color = available_colors[color_index]

    # Определение строки формата для colorlog
    log_format = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Создаем логгер с именем, соответствующим идентификатору аккаунта
    logger = colorlog.getLogger(str(account_id))
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Обработчик для вывода логов в консоль
        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = colorlog.ColoredFormatter(log_format, log_colors={
            'DEBUG': account_color,
            'INFO': account_color,
            'WARNING': account_color,
            'ERROR': account_color,
            'CRITICAL': 'red,bg_white',
        })
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.debug("Setting up logging for account ID: {}".format(account_id))
    return logger
