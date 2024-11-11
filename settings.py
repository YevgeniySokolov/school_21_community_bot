import os

# Время, по истечении которого регистрация прерывается, задается в часах
TIMER_USER_STEP = 6

# Настройки Метрик
STATES_COLLECTION = (
    'school21_nickname',
    'sber_id',
    'team_name',
    'role_level',
    'activity_description',
    'final_step',
)

# Админские команды
# для команды /dump имя файла
DUMP_FILE_NAME = "database_dump.json"

# настройка вывода списка (пагинация)
START_OFFSET = 0
LIMIT = 10

# канал сообщества, если не менять - подтягивается из .env
CHANNEL_ID = os.getenv("CHANNEL_ID")

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Время действия ссылки на переход в сообщество, задается в часах
TIME_EXPIRE_HOUR = 72
