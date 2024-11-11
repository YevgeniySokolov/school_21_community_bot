class LogMessage:

    # Общие информационные сообщения при логировании
    START_MSG: str = 'ЗАПУСК ПРИЛОЖЕНИЯ...'
    SUCCESSFULL_START: str = 'ВСЕ ПРИЛОЖЕНИЯ УСПЕШНО ЗАПУЩЕНЫ!'
    ROUTERS: str = 'МАРШРУТИЗАТОРЫ ПОДКЛЮЧЕНЫ...'
    MIDDLEWARES: str = 'ПОСРЕДНИКИ ПОДКЛЮЧЕНЫ...'
    BOT_UP: str = 'БОТ ЗАПУЩЕН!'
    GET_SESSION: str = 'СЕССИЯ ПОЛУЧЕНА'
    ERROR: str = 'НЕПРЕДВИДЕННАЯ ОШИБКА: {}'
    JOB_IS_DONE: str = 'ЗАДАЧА ВЫПОЛНЕНА!'

    # handlers
    USER_LINK: str = 'Пользователь {} подключен к боту!'
    USER_STATUS: str = "Пользователь {} зарегистрирован: {}, администратор: {}"
    GO_TO_REG: str = "Перенаправляем пользователя на ветку регистрации"
    GO_TO_CONTINUE_REG: str = (
        "Перенаправляем пользователя на продолжение регистрации")
    GO_TO_SEARCH: str = "Перенаправляем пользователя на ветку поиска"
    REG_COMPLETE: str = "Регистрация пользователя {} успешно завершена!"
    ALL_DATA_RECEIVED: str = " Все данные о пользователе {} успешно собраны!"
    USER_SAVED_TO_DB: str = "Пользователь {} успешно сохранен в базу данных!"
    CRYPT_BASE_REQUEST: str = (
        "Пользователь {} сделал запрос на шифрование/расшифровку базы данных!"
    )
    DUMP_BASE_REQUEST: str = (
        "Пользователь {} сделал запрос на дамп базы данных!"
    )
    NOT_ENOUGH_RIGHTS: str = (
        "У пользователя {} недостаточно прав на выполнение операции!"
    )

    # keyboards
    KEYBRD_IS_DONE: str = "Клавиатура подготовлена"

    # database
    START_INIT_DB: str = "Инициализация базы данных запущена"
    PRESETTING_VALUES: str = "Установка первичных значений базы данных..."