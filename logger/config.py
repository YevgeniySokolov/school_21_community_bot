import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# DEBUG, INFO, WARNING, ERROR, CRITICAL - уровни вывода логов
LOGGING_LEVEL = logging.INFO
LOG_FORMAT = (
    '%(asctime)s -%(name)s- [%(levelname)s] %(message)s | '
    'file %(filename)s: func(%(funcName)s), line(%(lineno)d)'
)
DT_FORMAT = '%d-%m-%Y_%H-%M-%S'
MAXBYTES = 10**6
BACKUP_COUNT = 5
