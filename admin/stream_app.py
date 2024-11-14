import asyncio
import os
import sys

import streamlit as st
from graphs import (plot_incomplete_registration_bar_chart,
                    plot_registration_stats,
                    plot_registration_status_distribution_in_users,
                    render_registered_users_roles_distribution_pie_chart,
                    render_user_level_distribution)
from stream_db import get_telegram_id, is_user_admin
from user_management import update_metrics
from user_visualization import (display_registration_time,
                                display_search_users, display_statics,
                                display_status_users, handle_user_actions)

from bot.decorators import db_session_decorator

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@db_session_decorator
async def display_header(session):
    """
    Асинхронная функция, отображающая заголовок интерфейса админ. панели
    Telegram-бота, а также метрики зарегистрированных и
    незавершивших регистрацию пользователей.
    Функция выполняет следующие действия:
    - отображает название бота в центре страницы;
    - подсчитывает и отображает количество зарегистрированных пользователей
    с зеленым цветом текста;
    - подсчитывает и отображает количество пользователей, которые прервали
    регистрацию, с красным цветом текста.
    Вся информация выводится с использованием markdown и HTML.
    Функция обновляет метрики в асинхронной сессии базы данных.
    """
    st.markdown(
        """
        <div style='text-align: center; margin-top: 10px;'>
            <h1 style='color: #666666;'><u>Telegram-бот - @название</u></h1>
        </div>
        <div style='margin-top: 30px;'></div>
        <hr style='border: 1px solid #cccccc; width: 100%; margin-top: 20px;'>
        """,
        unsafe_allow_html=True
    )
    # Обновление метрик
    db = session
    await update_metrics(db)
    # Настройки размера шрифта
    font_size_registered = 30
    font_size_abandoned = 30
    col1, col2 = st.columns(2)
    # Отображение зарегистрированных пользователей
    with col1:
        registered_users_value = st.session_state.registered_users
        st.markdown(
            (
                f"<div style='text-align: center;'>"
                f"Зарегистрированные пользователи:<br>"
                f"<span style='color: green; font-size: "
                f"{font_size_registered}px;'>"
                f"{registered_users_value}</span>"
                f"</div>"
            ),
            unsafe_allow_html=True
        )
    # Отображение незарегистрированных пользователей
    with col2:
        abandoned_users_value = st.session_state.abandoned_users
        span_style = (
            "<span style='color: red; "
            f"font-size: {font_size_abandoned}px;'>"
        )
        st.markdown(
            f"""
            <div style='text-align: center;'>
                Пользователи, прервавшие регистрацию:<br>
                {span_style}
                    {abandoned_users_value}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    # Добавление серой линии после колонок
    st.markdown(
        """
        <hr style='border: 1px solid #cccccc; width: 100%; margin-top: 20px;'>
        """,
        unsafe_allow_html=True
    )


async def display_sidebar():
    """
    Асинхронная функция для отображения боковой панели управления в приложении.
    Функция создает интерфейс боковой панели с заголовком и радио-кнопками для
    выбора различных действий, связанных с пользователями.
    В зависимости от выбранного действия вызываются соответствующие функции
    для отображения данных или выполнения операций с пользователями.
    """
    st.sidebar.markdown(
        "<h1 style='text-align: left; color: #4CAF50;'>Панель управления</h1>",
        unsafe_allow_html=True
    )
    blocks = {
        "Информация о пользователях": [
            "Не выбрано",
            "Все пользователи",
            "Зарегистрированные пользователи",
            "Незарегистрированные пользователи",
            "Карточка пользователя"
        ],
        "Управление пользователями": [
            "Не выбрано",
            "Добавить пользователя",
            "Редактировать пользователя",
            "Удалить пользователя",
        ],
        "Анализ данных": [
            "Не выбрано",
            "Динамика регистрации",
            "Метрики незавершенной регистрации",
            "Линейный график: 'Динамика конверсии регистрации'.",
            "График: 'Анализ точек прерывания регистрации.'",
            "Диаграмма: 'Распределение зарегистрированных "
            "пользователей по уровням.'",
            "Диаграмма: 'Распределения зарегистрированных "
            "пользователей по ролям.'",
            "Диаграмма: 'Зарегистрированные и "
            "незарегистрированные пользователи.'",
        ],
    }
    action_handlers = {
        "Зарегистрированные пользователи": display_status_users,
        "Незарегистрированные пользователи": display_status_users,
        "Все пользователи": display_status_users,
        "Карточка пользователя": display_search_users,
        "Добавить пользователя": handle_user_actions,
        "Редактировать пользователя": handle_user_actions,
        "Удалить пользователя": handle_user_actions,
        "Динамика регистрации": display_registration_time,
        "Метрики незавершенной регистрации": display_statics,
        "Линейный график: "
        "'Динамика конверсии регистрации'.": plot_registration_stats,
        "График: 'Анализ точек прерывания регистрации.'": (
            plot_incomplete_registration_bar_chart),
        "Диаграмма: 'Распределение зарегистрированных "
        "пользователей по уровням.'": (
            render_user_level_distribution),
        "Диаграмма: 'Распределения зарегистрированных "
        "пользователей по ролям.'": (
            render_registered_users_roles_distribution_pie_chart),
        "Диаграмма: 'Зарегистрированные и "
        "незарегистрированные пользователи.'": (
            plot_registration_status_distribution_in_users),
    }
    selected_block = st.sidebar.selectbox("", list(blocks.keys()))
    selected_action = "Не выбрано"
    if selected_block:
        selected_action = st.sidebar.radio("", blocks[selected_block])
        if selected_action != "Не выбрано":
            if selected_action in action_handlers:
                task = asyncio.create_task(
                    action_handlers[selected_action](selected_action)
                )  # Запускаем в отдельной задаче
                try:
                    await task  # Ожидаем завершения задачи
                except Exception as e:
                    st.exception(e)  # Выводим ошибку, если произошла
            else:
                st.warning(f"Действие '{selected_action}' не найдено.")


@db_session_decorator
async def main(session):
    """
    Основная асинхронная функция приложения.
    Эта функция отвечает за аутентификацию, инициализацию и отображение
    пользовательского интерфейса. Она вызывает функции для отображения
    заголовка и боковой панели управления.
    """
    await display_header()
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    username = st.sidebar.text_input(
        "Введите имя пользователя в Telegram",
        help="Введите Ваше имя пользователя в Telegram."
    )
    # Получаем параметр telegram_id из URL
    query_params = st.query_params
    telegram_id_from_url = query_params.get('telegram_id', [None])[0]

    if st.sidebar.button("Получить доступ"):
        db = session
        telegram_id_from_db = await get_telegram_id(username, db)
        # Проверяем, является ли пользователь администратором
        is_admin = await is_user_admin(username, db)

        if telegram_id_from_url:
            # Если telegram_id совпадает
            if telegram_id_from_url == telegram_id_from_db:
                st.session_state.is_authenticated = True
                st.success("Добро пожаловать, администратор!")
            else:
                st.error("У Вас нет прав доступа к этой странице.")
        else:
            if is_admin:  # Если пользователь администратор, разрешаем доступ
                st.session_state.is_authenticated = True
                st.success("Добро пожаловать, администратор!")
            else:
                st.error("У Вас нет прав доступа к этой странице.")

    if st.session_state.is_authenticated:
        await display_sidebar()


if __name__ == "__main__":
    asyncio.run(main())
