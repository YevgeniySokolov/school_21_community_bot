class ValidatorsIntValues:

    SCHOOL21NICKNAME_MAX_LEN = 16
    SBER_ID_TEAM_NAME_MAX_LEN = 256
    DESCRIPTION_MAX_LEN = 1024
    SCHOOL21NICKNAME_MIN_LEN = 4
    ALL_MIN_LEN = 0


class ValidatorsStrValues:

    SUPPORT_EMAIL = "<email@example.com>"
    LATIN_ONLY_PATTERN = "^[a-zA-Z]+$"
    SBER_ID_PATTERN = (
        r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]+"
        r"(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]+)*$"
    )
    ROLE_PATTERN = r"^([а-яА-Яa-zA-Z\-]+)(?:\s+([а-яА-Яa-zA-Z\- ]+))?$"
    ROLE_LEVELS = ("Junior", "Middle", "Senior", "Lead", "Стажер")


class ValidatorsMessages:

    SCHOOL21NICKNAME_LEN_ERROR = (
        "Никнейм школы 21 должен содержать от 4 до 16 символов.\n"
        "Пожалуйста, укажите корректный никнейм Школы 21."
    )
    SBER_ID_LEN_ERROR = (
        "Имя пользователя в СберЧате не должно быть пустым и превышать 256 символов.\n"
        "Пожалуйста, укажите корректное имя пользователя в СберЧате."
    )
    DESCRIPTION_LEN_ERROR = (
        "Размер описания вашей работы превышает допустимый лимит.\n"
        "Пожалуйста, сократите описание до 1024 символов."
    )
    TEAM_NAME_LEN_ERROR = (
        "Название команды не должно быть пустым и превышать 256 символов.\n"
        "Пожалуйста, укажите корректное название команды."
    )
    LATIN_ERROR = (
        "Никнейм Школы 21 может содержать только латинские буквы.\n"
        "Пожалуйста, укажите никнейм Школы 21."
    )
    SBER_ID_ERROR = (
        "Имя пользователя в СберЧате содержит недопустимые символы.\n"
        "Пожалуйста, укажите корректное имя пользователя в СберЧате."
    )
    SCHOOL21NICKNAME_EXIST_ERROR = (
        f"Такой пользователь уже есть. Поищи канал в списке своих чатов\n"
        f"или напиши нам на почту: {ValidatorsStrValues.SUPPORT_EMAIL}."
    )
    ROLE_ERROR = (
        "Введите, пожалуйста, корректный уровень и роль через пробел\n"
        "Например, Senior python разработчик"
    )
