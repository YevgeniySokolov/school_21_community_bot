# Бот [Школы 21](https://21-school.ru/) от Сбера


## Содержание
- [Общий обзор функционала](#общий-обзор-функционала)
- [Стэк используемых технологий](#стэк-используемых-технологий)
- [Регистрация пользователей](#регистрация-пользователей)
- [Панель администратора](#панель-администратора)
- [Поиск и просмотр членов коммьюнити](#поиск-и-просмотр-членов-коммьюнити)
- [Визуализация и аналитика](#визуализация-и-аналитика)
- [Дополнительные функции](#дополнительные-функции)
- [Деплой репозитория проекта на сервер](#деплой-репозитория-проекта-на-сервер)
- [Работа с Docker](#работа-с-docker)
- [Запуск админ. панели](#запуск-админ-панели)
- [Запуск тестов](#запуск-тестов)
- [Содержимое .env-файла](#содержимое-env-файла)
- [Дальнейшее развитие проекта](#дальнейшее-развитие-проекта)
- [Авторы проекта](#авторы-проекта)

## Общий обзор функционала
Telegram-робот Школы 21 позволяет:
- зарегистрироваться и перейти в коммьюнити Школы;
- осуществлять поиск сотрудников;
- управлять и анализировать данные (администратору).

## Стэк используемых технологий
- aiogram;
- aiosqlite;
- pandas;
- streamlit;
- matplotlib;
- seaborn;
- sqlalchemy;
- alembic;
- docker;
- nginx;
- pytest;
- flake8
- isort.

## Регистрация пользователей
*Старт*

Пользователь запускает команду /start, после чего бот определяет, зарегистрирован ли пользователь, и предлагает продолжить или возобновить регистрацию.

*Шаги регистрации*

Регистрация происходит поэтапно с запросом данных:
- никнейм в Школе 21;
- никнейм в СберЧате;
- название команды;
- роль и уровень;
- описание активности.

*Таймер прерывания*

Включается таймер, который отслеживает процесс регистрации. 
При отсутствии действий бот сохраняет текущие данные с пометкой, что регистрация не завершена.
Также у пользователя есть возможность возобновить регистрацию с того места, где он остановился, или начать процесс регистрации заново.

## Панель администратора
Администратор может войти в панель управления для выполнения специальных команд 
(доступ контролируется с помощью декоратора admin_required).

*Шифрование и дешифрование данных*

Администратор может зашифровать или расшифровать данные пользователей для защиты информации.

*Импорт и экспорт данных*

Возможен экспорт данных о пользователях в JSON-формате и последующий импорт с проверкой на дубликаты и корректность данных.

## Поиск и просмотр членов коммьюнити

*Поиск по ролям и уровням*

Пользователь может находить других членов коммьюнити, фильтруя их по роли и уровню.

*Карточка пользователя*

При выборе конкретного пользователя бот отображает информацию о нём, 
включая никнейм в Школе 21, никнейм в Сберчате , команду и роль.

## Визуализация и аналитика
*Административная панель Streamlit*

Визуальная админ. панель отображает метрики по пользователям, включая распределение по ролям, уровням и статусам регистрации.

*Графики*

Реализованы функции для построения различных графиков (к примеру, распределение ролей, уровней, динамика регистрации), что помогает администратору видеть текущую активность и конверсию пользователей.

## Дополнительные функции
*Создание индивидуальных одноразовых ссылок на коммьюнити*

Бот может создавать временные ссылки для приглашения пользователей в сообщество.

*Анализ незавершенной регистрации*

Панель администратора показывает статистику по точкам, на которых пользователи чаще всего прерывают регистрацию.

*Логирование*

Весь процесс работы бота логируется.

## Деплой репозитория проекта на сервер
```
rsync -avz --exclude "venv" -e "ssh -i <ваш ssh ключ>" 
/<путь к вашему локальному проекту>/
<имя пользователя>@<IP адрес>:/путь к вашему проекту на сервере/
```

## Работа с Docker
*Сначала собираем контейнеры:*
```
docker-compose build --no-cache
```

*Затем запускаем в фоновом режиме:*
```
docker-compose up -d
```

## Запуск админ. панели
В случае отсутствия контейнеров

*Убедитесь, что установлены дополнительные зависимости (они добавлены в requirements.txt):*
```
- streamlit==1.39.0;
- matplotlib==3.9.2.
```
*В корневой директории проекта выполните следующую команду:*
```
streamlit run admin/stream_app.py
```

## Запуск тестов
*Из корневой директории проекта выполните следующую команду:* 
```
python -m pytest --cache-clear
```

## Содержимое .env-файла
Файл должен быть расположен в корневой директории
```
DATABASE_URL=sqlite+aiosqlite:///./database/test.db
TELEGRAM_TOKEN=<Токен Вашего Telegram-бота>
CHANNEL_ID=<Ваш ID Telegram-канала>
ALEMBIC_CONFIG=/app/database/alembic.ini
```
Бот должен состоять и иметь в Telegram-канале админские права. 

## Дальнейшее развитие проекта
- переход на PostgreSQL;
- изменение схемы поиска сотрудников;
- CI/CD;
- автоматизация шифрования и дешифрования базы данных;
- добавление API для интеграции с другими системами.
- команда /support для перехода пользователя на портал или форму технической поддержки.

## 👥 Авторы проекта

| 👤 Автор            | 💼 Должность        | ✉️ E-mail                       | 🔗 GitHub                                            |
|---------------------|----------------------|---------------------------------|-------------------------------------------------------|
| Артем Чебыкин       | Python Developer     | chebykin.ag@yandex.ru           | [m0t0r0v](https://github.com/m0t0r0v)                 |
| Денис Фадеев        | Python Developer     | denfizzz1978@yandex.ru          | [Denfizzz](https://github.com/Denfizzz)               |
| Артем Шенин         | Python Developer     | rassada2021@yandex.ru           | [Artem-SPb](https://github.com/Artem-SPb)             |
| Петр Виноградов     | Python Developer     | petrowaw@yandex.ru              | [PeterFVin](https://github.com/PeterFVin)             |
| Денис Смирнов       | Python Developer     | smirnov.denis900@yandex.ru      | [dxndigiden](https://github.com/dxndigiden)           |
| Евгений Соколов     | Team Lead            | ea.sokolov.87@yandex.ru         | [YevgeniySokolov](https://github.com/YevgeniySokolov) |
