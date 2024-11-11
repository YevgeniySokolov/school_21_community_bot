from datetime import datetime

import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError
from stream_db import add_user, delete_user_by_telegram_id, update_user
from user_management import (fetch_all_users, fetch_registered_users,
                             fetch_unregistered_users,
                             fetch_user_by_telegram_id,
                             incomplete_registration_stats,
                             registration_stats_by_date)

from bot.decorators import db_session_decorator
from bot.utils import parse_level_and_role
from logger.config import DT_FORMAT


@db_session_decorator
async def display_status_users(action_option_1, session):
    db = session
    """
    Отображение списка пользователей в зависимости от выбранного действия.
    Параметры:
    - action_option_1 (str): Выбор действия для отображения
    (все пользователи, зарегистрированные или незарегистрированные).
    Принимает данные из базы данных, фильтрует пользователей
    по выбранным критериям (команда, роль, уровень)
    и отображает информацию в виде таблицы через Streamlit.
    """
    users = []
    if action_option_1 == "Все пользователи":
        users = await fetch_all_users(db)
    elif action_option_1 == "Зарегистрированные пользователи":
        users = await fetch_registered_users(db)
    else:
        users = await fetch_unregistered_users(db)
    if users:
        st.markdown(
            f"<h2 style='color: #66b3ff;'>{action_option_1}</h2>",
            unsafe_allow_html=True
        )
        user_data = [{
            "ID": user.id,
            "Username": user.username,
            "Telegram ID": user.telegram_id,
            "Sber_ID": user.sber_id,
            "Ник в school_21": user.school21_nickname,
            "Команда": user.team_name,
            "Роль": user.role,
            "Уровень": user.level.name,
            "Чем занимается": user.description,
            "Дата регистрации": (
                user.registration_date.strftime(DT_FORMAT)
            ),
            "Администратор": user.is_admin,
            "Зарегестрирован": user.is_registered,
            "Прервано на поле": (
                "Все поля заполнены!"
                if user.is_registered else user.field_not_filled
            )
        } for user in users]
        # Создаём DataFrame
        df = pd.DataFrame(user_data)
        # Добавляем селекторы для фильтрации
        team_options = df['Команда'].unique().tolist()
        role_options = df['Роль'].unique().tolist()
        level_options = df['Уровень'].unique().tolist()
        interrupted_fields = df['Прервано на поле'].unique().tolist()
        selected_team = st.selectbox(
            "Выберите команду:", ["Все команды"] + team_options
        )
        selected_role = st.selectbox(
            "Выберите роль:", ["Все роли"] + role_options
        )
        selected_level = st.selectbox(
            "Выберите уровень:", ["Все уровни"] + level_options
        )
        selected_interrupted_field = st.selectbox(
            "Выберите поле перед которым прервался процесс регистрации:",
            ["Получить все данные"] + interrupted_fields
        )
        # Фильтрация по команде
        if selected_team != "Все команды":
            df = df[df['Команда'] == selected_team]
        # Фильтрация по роли
        if selected_role != "Все роли":
            df = df[df['Роль'] == selected_role]
        # Фильтрация по уровню
        if selected_level != "Все уровни":
            df = df[df['Уровень'] == selected_level]
        # Фильтрация по этапу прерывания
        if selected_interrupted_field != "Получить все данные":
            df = df[df['Прервано на поле'] == selected_interrupted_field]
        # Фильтрация по этапу прерывания
        if selected_interrupted_field != "Получить все данные":
            df = df[df['Прервано на поле'] == selected_interrupted_field]
        # Пагинация
        page_size = st.selectbox(
            "Количество пользователей на странице:", [5, 10, 15, 20, 100]
        )
        total_users = df.shape[0]
        # округление вверх
        total_pages = (total_users + page_size - 1) // page_size
        max_pages = max(1, total_pages)  # Гарантируем, что max_pages >= 1
        current_page = st.number_input(
            "Страница:", min_value=1, max_value=max_pages, value=1
        )
        # Вычисление индексов для отображения на текущей странице
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size
        page_data = df.iloc[start_index:end_index]
        # Отображение таблицы
        page_data['Telegram ID'] = page_data['Telegram ID'].astype(str)
        st.dataframe(
            page_data.style, hide_index=True
        )
    else:
        st.write("Пользователи не найдены.")


@db_session_decorator
async def display_search_users(action_option, session):
    db = session
    """
    Отображение карточки пользователя по его Telegram ID.
    Параметры:
    - action_option_1 (str): Выбор действия,
    в данном случае "Карточка пользователя".
    Функция позволяет пользователю ввести Telegram ID
    и получить информацию о соответствующем пользователе из базы данных.
    Результаты отображаются в виде таблицы через Streamlit.
    Если пользователь не найден, выводится ошибка.
    """
    user_card = (
        "<h3 style='color: #4CAF50; font-size: 36px;'>"
        "Карточка пользователя"
        "</h3>"
    )
    find_user_by_telegram_id = (
        "<h2 style='color: #66b3ff;'>Карточка пользователя</h2>"
    )
    if action_option == "Карточка пользователя":
        st.markdown(
            find_user_by_telegram_id,
            unsafe_allow_html=True
        )
        telegram_id = st.number_input(
            "Введите Telegram_ID пользователя:",
            help="Введите Telegram_ ID пользователя.",
            key="telegram_id_input",
            min_value=0,
            step=1
        )
        if st.button("Получить данные", key="get_data_button"):
            user = await fetch_user_by_telegram_id(db, telegram_id)
            if user:
                user_data = {
                    "Сберчат:": user.sber_id,
                    "TG": user.username,
                    "S21": user.school21_nickname,
                    "Роль": user.role,
                    "Над чем работает": user.description,
                }
                # Преобразуем словарь в DataFrame
                df = pd.DataFrame(
                    list(user_data.items()),
                    columns=["Параметр", "Значение"]
                )
                st.markdown(
                    user_card,
                    unsafe_allow_html=True
                )
                # Отображаем DataFrame без индексов
                st.dataframe(df, hide_index=True)
                st.success(
                    f"Данные пользователя {user.username} с telegram_id = "
                    f"{telegram_id} загружены."
                )
            else:
                st.error("Пользователь не найден.")


@db_session_decorator
async def handle_user_actions(action_option, session):
    db = session
    """
    Обработка действий пользователя: добавление,
    редактирование или удаление пользователя.
    Параметры:
    - action_option_2 (str): Выбранное действие.
    Возможные значения: "Добавить пользователя",
    "Редактировать пользователя", "Удалить пользователя".
    В зависимости от выбранного действия, отображает соответствующую форму
    для ввода данных пользователя, загружает и отображает данные существующего
    пользователя или удаляет пользователя из базы данных.
    Все взаимодействия выполнены через Streamlit.
    """
    if action_option == "Добавить пользователя":
        st.markdown(
            "<h2 style='color: #66b3ff;'>Добавить нового пользователя</h2>",
            unsafe_allow_html=True
        )
        with st.form(key="add_user_form"):
            username = st.text_input(
                "Введите имя пользователя в Telegram:",
                help="Введите имя пользователя в Telegram."
            )
            telegram_id = st.number_input(
                "Введите Telegram ID:",
                help="Введите Telegram ID.",
                min_value=0,
                step=1
            )
            sber_id = st.text_input(
                "Введите имя пользователя в Сберчат:",
                help=(
                    "Имя пользователя в Сберчат - это часть адреса "
                    "электронной почты до знака '@'."
                ),
            )
            school21_nickname = st.text_input(
                "Введите ник в Школе 21:",
                help="Введите ник в Школе 21."
            )
            team_name = st.text_input(
                "Укажите команду:",
                help="Например: Lab.SberPay.NFC "
                "или Lab.Платежный счет.Продукт."
            )
            description = st.text_input(
                "Введите, чем занимается участник:",
                help="Введите, чем занимается участник в команде."
            )
            role_level = st.text_input(
                "Пожалуйста, введите роль строго, как в Пульсе:",
                help="Например: Senior golang разработчик."
            )
            is_admin = st.checkbox(
                "Является администратором:",
                help="Укажите, является участник администратором или нет."
            )
            submit_button = st.form_submit_button(label="Добавить")
            if submit_button:
                required_fields = {
                    "'Имя пользователя в Telegram'": username,
                    "'Telegram ID'": telegram_id,
                    "'Имя пользователя в Сберчат'": sber_id,
                    "'Ник в Школе 21'": school21_nickname,
                    "'Укажите команду'": team_name,
                    "'Роль'": role_level,
                }
                missing_fields = [
                    field for field,
                    value in required_fields.items() if not value
                ]
                try:
                    if missing_fields:
                        raise ValueError(
                            "Пожалуйста, заполните следующие "
                            f"обязательные поля: {', '.join(missing_fields)}."
                        )
                    else:
                        level_id, role = await parse_level_and_role(
                            role_level, db
                        )
                        registration_date = datetime.now()
                        is_registered = True
                        try:
                            await add_user(
                                db,
                                telegram_id,
                                username,
                                sber_id,
                                team_name,
                                level_id,
                                description,
                                registration_date,
                                school21_nickname,
                                is_admin,
                                is_registered,
                                role,
                            )
                            st.success("Пользователь успешно добавлен!")
                        except IntegrityError as e:
                            db.rollback()  # Отменяем изменения в случае ошибки
                            # Сопоставление ошибок с сообщениями
                            error_messages = {
                                'telegram_id':
                                "Пользователь с данным Telegram ID "
                                "уже существует.",
                                'username':
                                "Пользователь с таким именем в Telegram "
                                "уже существует.",
                                'sber_id':
                                "Пользователь с таким именем пользователя "
                                "в Сберчат уже существует.",
                                'school21_nickname':
                                "Пользователь с таким ником в Школе 21 уже "
                                "существует."
                            }
                            # Проверяем, есть ли ошибка в словаре
                            matching_keys = [
                                key for key in error_messages
                                if key in str(e.orig)
                            ]
                            error_key = next(iter(matching_keys), None)
                            if error_key:
                                st.error(error_messages[error_key])
                except ValueError as e:
                    st.error(str(e))
    elif action_option == "Редактировать пользователя":
        st.markdown(
            "<h2 style='color: #66b3ff;'>Редактировать пользователя</h2>",
            unsafe_allow_html=True
        )
        telegram_id = st.number_input(
            "Введите Telegram ID пользователя:",
            help="Введите Telegram ID пользователя.",
            min_value=0,
            step=1
        )
        if st.button("Получить данные"):
            user = await fetch_user_by_telegram_id(db, telegram_id)
            if not user:
                st.error("Пользователь не найден.")
                st.session_state.pop("user_data", None)
                return  # Выходим из функции, если пользователь не найден
            st.session_state.user_data = user
            st.success(
                f"Данные пользователя {user.username} "
                f"с Telegram ID = {user.telegram_id} загружены."
            )
            st.markdown(
                "<span style='color: red;'>ВНИМАНИЕ<br/>"
                f"Вы редактируете данные участника {user.username}, "
                "у которого Telegram ID "
                f"в базе данных = {user.telegram_id}.</span>",
                unsafe_allow_html=True
            )
        if "user_data" in st.session_state:
            with st.form(key="edit_user_form"):
                user = st.session_state.user_data
                if user:
                    is_admin = st.checkbox(
                        "Является администратором",
                        help=(
                            "Укажите, является участник "
                            "администратором или нет."
                        ),
                        value=user.is_admin
                    )
                    submit_button = st.form_submit_button(
                        label="Сохранить изменения"
                    )
                    if submit_button:
                        if user.is_admin != is_admin:
                            updated_user = {"is_admin": is_admin}
                            success = await update_user(
                                db, user.id, updated_user
                            )
                            if success:
                                st.success(
                                    "Данные пользователя успешно обновлены!"
                                )
                                user.is_admin = is_admin
                                st.session_state.user_data = user
                            else:
                                st.error(
                                    "Не удалось обновить данные пользователя."
                                )
                        else:
                            st.warning(
                                "У пользователя уже установлен такой статус!"
                            )
    else:
        st.markdown(
            "<h2 style='color: #66b3ff;'>Удалить пользователя</h2>",
            unsafe_allow_html=True
        )
        telegram_id = st.number_input(
            "Введите Telegram ID пользователя:",
            help="Введите Telegram ID пользователя.",
            key="telegram_id_input_delete",
            min_value=0,
            step=1
        )
        # Добавляем переменную состояния
        if 'show_delete_button' not in st.session_state:
            st.session_state.show_delete_button = False
        if st.button("Получить данные"):
            user = await fetch_user_by_telegram_id(db, telegram_id)
            if user:
                user_data = {
                    "Сберчат:": user.sber_id,
                    "TG": user.username,
                    "S21": user.school21_nickname,
                    "Роль": user.role,
                    "Над чем работает": user.description,
                }
                # Преобразуем словарь в DataFrame
                df = pd.DataFrame(
                    list(user_data.items()),
                    columns=["Параметр", "Значение"]
                )
                st.markdown(
                    "<h3 style='color: #4CAF50; font-size: 36px;'>"
                    "Карточка пользователя</h3>",
                    unsafe_allow_html=True
                )
                # Отображаем DataFrame без индексов
                st.dataframe(df, hide_index=True)
                st.success(
                    f"Данные пользователя {user.username} с Telegram ID = "
                    f"{telegram_id} загружены."
                )
                st.markdown(
                    "<span style='color: red;'>"
                    "ВНИМАНИЕ<br/>Вы собираетесь удалить "
                    f"участника {user.username} "
                    f"у которого Telegram ID в "
                    f"базе данных = {user.telegram_id}.<br/>"
                    "Если вы уверены, нажмите кнопку УДАЛИТЬ.</span>",
                    unsafe_allow_html=True
                )
                # Включаем кнопку удаления
                st.session_state.show_delete_button = True
            else:
                st.error("Пользователь не найден.")
        # Условие для отображения кнопки "Удалить"
        if st.session_state.show_delete_button:
            if st.button("Удалить"):
                success = await delete_user_by_telegram_id(db, telegram_id)
                if success:
                    st.success("Пользователь успешно удален!")
                    # Скрываем кнопку после удаления
                    st.session_state.show_delete_button = False
                else:
                    st.error("Пользователь не найден.")
        # Если пользователь уже удален, можем очистить информацию о нем
        if not st.session_state.show_delete_button:
            st.session_state.user_data = None


@db_session_decorator
async def display_statics(action_option, session):
    db = session
    if action_option == "Метрики незавершенной регистрации":
        stats = await incomplete_registration_stats(db)
    if stats:
        st.markdown(
            f"<h2 style='color: #66b3ff;'>{action_option}</h2>",
            unsafe_allow_html=True
        )
        statics_data = [
            {
                "Прервано на поле": field,
                "Количество": count,
                "В процентах": percentage
            } for field, (count, percentage) in stats.items()
        ]
        # Создаём DataFrame
        df = pd.DataFrame(statics_data)
        # Пагинация
        rows_per_page_options = [5, 10, 15, 20, 50, 100]
        rows_per_page = st.selectbox(
            "Количество строк на странице:",
            rows_per_page_options,
            index=0
        )
        total_rows = len(df)
        num_pages = (total_rows + rows_per_page - 1) // rows_per_page
        if num_pages > 1:
            page_number = st.slider("Страница", 1, num_pages, 1)
            start_index = (page_number - 1) * rows_per_page
            end_index = min(start_index + rows_per_page, total_rows)
            paginated_df = df[start_index:end_index]
            st.dataframe(paginated_df, hide_index=True)
        else:
            st.dataframe(df, hide_index=True)


@db_session_decorator
async def display_registration_time(action_option, session):
    db = session
    if action_option == "Динамика регистрации":
        stats = await registration_stats_by_date(db)
        if stats:
            st.markdown(
                f"<h2 style='color: #66b3ff;'>{action_option}</h2>",
                unsafe_allow_html=True
            )
            statics_data = [
                {
                    "Дата": field,
                    "Всего пользователей": data["total_users"],
                    "Зарегистрированные": data["registered_users"],
                    "Незарегистрированные": data["unregistered_users"],
                    "Конверсия (в %)": data["conversion_rate"]
                } for field, data in stats.items()
            ]
            # Создаём DataFrame
            df = pd.DataFrame(statics_data)
            # Пагинация (остаётся без изменений)
            rows_per_page_options = [5, 10, 15, 20, 50, 100]
            rows_per_page = st.selectbox(
                "Количество строк на странице:",
                rows_per_page_options,
                index=0
            )
            total_rows = len(df)
            num_pages = (total_rows + rows_per_page - 1) // rows_per_page
            if num_pages > 1:
                page_number = st.slider("Страница", 1, num_pages, 1)
                start_index = (page_number - 1) * rows_per_page
                end_index = min(start_index + rows_per_page, total_rows)
                paginated_df = df[start_index:end_index]
                st.dataframe(paginated_df, hide_index=True)
            else:
                st.dataframe(df, hide_index=True)
