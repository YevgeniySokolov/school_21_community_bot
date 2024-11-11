import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns
import streamlit as st
from stream_db import get_user_counts_by_level
from user_management import (fetch_all_users, fetch_registered_users,
                             incomplete_registration_stats,
                             registration_stats_by_date)

from bot.decorators import db_session_decorator


@db_session_decorator
async def render_user_level_distribution(action_option, **kwargs):
    """
    Отображение круговой диаграммы распределения
    зарегистрированных пользователей по уровням.
    """
    session = kwargs['session']
    users = await fetch_registered_users(session)
    if not users:
        st.write("Нет пользователей.")
        return
    level_counts = get_user_counts_by_level(users)
    # Получение данных для круговой диаграммы
    levels = list(map(str, level_counts.keys()))
    counts = list(map(int, level_counts.values()))
    # Построение круговой диаграммы
    fig = plt.figure(figsize=(10, 6))
    plt.pie(
        counts,
        labels=levels,
        autopct='%1.1f%%',
        startangle=90
    )
    plt.title('Распределение пользователей по уровням', color='green')
    plt.tight_layout()  # Добавляем эту строку
    fig.set_size_inches(10, 6)  # Устанавливаем размер
    st.pyplot(fig)


@db_session_decorator
async def render_registered_users_roles_distribution_pie_chart(
    action_option, **kwargs
):
    """
    Отображает распределение ролей среди зарегистрированных пользователей
    в виде круговой диаграммы.
    """
    session = kwargs['session']
    users = await fetch_registered_users(session)
    if not users:
        st.write("Нет зарегистрированных пользователей.")
        return
    # Сбор статистики по ролям
    roles_count = {}
    for user in users:
        role = user.role
        roles_count[role] = roles_count.get(role, 0) + 1
    # Преобразуем в DataFrame
    df = pd.DataFrame(
        list(roles_count.items()), columns=['Роль', 'Количество']
    )
    # Построение круговой диаграммы
    fig = plt.figure(figsize=(10, 6))
    plt.pie(
        df['Количество'],
        labels=df['Роль'],
        autopct='%1.1f%%',
        startangle=90
    )
    plt.title('Распределение пользователей по уровням', color='green')
    plt.tight_layout()  # Добавляем эту строку
    fig.set_size_inches(10, 6)  # Устанавливаем размер
    st.pyplot(fig)


@db_session_decorator
async def plot_registration_status_distribution_in_users(
    action_option, **kwargs
):
    """
    Отображает распределение пользователей по статусу регистрации
    (зарегистрированные и незарегистрированные) в виде круговой диаграммы.
    """
    session = kwargs['session']
    users = await fetch_all_users(session)
    if not users:
        st.write("Нет пользователей.")
        return
    # Сбор статистики по статусу регистрации
    registered_count = sum(1 for user in users if user.is_registered)
    unregistered_count = len(users) - registered_count
    counts = [registered_count, unregistered_count]
    labels = ['Зарегистрированные', 'Незарегистрированные']
    # Построение круговой диаграммы
    fig = plt.figure(figsize=(10, 6))
    wedges, texts, autotexts = plt.pie(
        counts,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=['#66b3ff', '#ff9999'],
        textprops=dict(color="black")  # Цвет текста названий
    )
    # Настройка цвета текста для процентных значений
    for text in autotexts:
        text.set_color("black")  # Цвет для процентов
        text.set_fontsize(12)  # Размер шрифта для процентов
    # Устанавливаем стиль названия
    plt.title(
        "Диаграмма 'Зарегистрированные / Незарегистрированные' пользователи",
        color='green',
        loc='center'  # Центрируем заголовок
    )
    plt.tight_layout()  # Добавляем эту строку
    fig.set_size_inches(10, 6)
    # Отображение в Streamlit
    st.pyplot(plt)


@db_session_decorator
async def plot_incomplete_registration_bar_chart(action_option, session):
    mapping = {
        "school21_nickname": "Ник в Школе 21.",
        "sber_id": "Имя в СберЧате.",
        "username": "Ник в Telegram.",
        "team_name": "Укажи команду.",
        "role": "Укажи роль."
    }
    db = session
    stats = await incomplete_registration_stats(db)
    if not stats:
        st.write("Нет данных для отображения.")
        return
    df = pd.DataFrame.from_dict(
        stats, orient='index', columns=['count', 'percentage']
    )
    df.index.name = 'field_value'
    df.reset_index(inplace=True)
    # Обработка None значений в field_value
    df['field_value'] = df['field_value'].fillna('Не указано')
    df['field_value'] = df['field_value'].astype(str)
    df['user_friendly_label'] = (
        df['field_value'].map(mapping).fillna(df['field_value'])
    )
    # Сортировка столбцов по возрастанию
    # (если добавить ascending=False - будет по убыванию)
    df = df.sort_values(by=['count'])
    fig, ax = plt.subplots()
    colors = []
    for count in df['count']:
        if count > 5:  # Пример: красный цвет для значений больше 5
            colors.append('red')
        else:
            colors.append('green')
    ax.bar(df['user_friendly_label'], df['count'], color=colors)
    ax.set_xlabel(
        "Этап, на котором пользователь прервал регистрацию.",
        color='#66b3ff'
    )
    ax.set_ylabel("Количество пользователей.", color='#66b3ff')
    ax.set_title(
        "Анализ точек прерывания регистрации.", color='green'
    )
    # Форматирование оси Y для отображения целых чисел
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


@db_session_decorator
async def plot_registration_stats(action_option, session):
    """
    Строит график конверсии регистрации пользователей.
    """
    db = session
    stats = await registration_stats_by_date(db)
    if not stats:
        return
    df = pd.DataFrame.from_dict(stats, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()  # Сортируем по дате
    df['conversion_rate'] = df['conversion_rate'].round(2)
    fig, ax = plt.subplots(figsize=(12, 6))
    # Используем seaborn для более красивого графика
    sns.set_style("whitegrid")  # Устанавливаем стиль сетки
    sns.lineplot(
        x=df.index,
        y='conversion_rate',
        data=df,
        ax=ax,
        marker='o',
        linewidth=2,
        color="green"
    )
    ax.set_xlabel('Дата регистрации', fontsize=18, color="red")
    ax.set_ylabel('Конверсия (%)', fontsize=18, color="red")
    ax.tick_params(axis='x', rotation=45)
    # Выравниваем метки по правому краю
    labels = ax.get_xticklabels()
    ax.set_xticklabels(labels, ha='right')
    # Добавляем сетку для лучшей читаемости
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.title('Динамика конверсии регистрации', fontsize=24, color="Green")
    plt.tight_layout()
    st.pyplot(fig)
