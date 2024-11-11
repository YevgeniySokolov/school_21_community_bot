import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from .config import (BACKUP_COUNT, BASE_DIR, DT_FORMAT, LOG_FORMAT,
                     LOGGING_LEVEL, MAXBYTES)

filename = f'{datetime.now().strftime(DT_FORMAT)}_logfile.log'


def configure_logging():
    """
    Базовая конфигурация логирования.
    """
    log_dir = BASE_DIR / 'logfiles'
    try:
        log_dir.mkdir(exist_ok=True)
    except OSError as e:
        print(f"Ошибка при создании директории логов: {e}")
        return
    log_file = log_dir / filename
    rotating_handler = RotatingFileHandler(
        log_file, maxBytes=MAXBYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=LOGGING_LEVEL,
        handlers=(rotating_handler, logging.StreamHandler())
    )
