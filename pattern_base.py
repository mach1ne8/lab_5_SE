from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
import pandas as pd
from datetime import datetime, timedelta


def parse_schedule(week_type: str):
    file_schedule = '2_курс_четная.xlsx' if week_type == "2 нед." else '2_курс_нечетная.xlsx'
    return pd.read_excel(file_schedule, sheet_name=None)


def get_course_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for i in range(1, 5):
        builder.row(
            types.InlineKeyboardButton(text=str(i), callback_data=f"course_{i}")
        )
    builder.adjust(1)
    return builder.as_markup()


def get_group_kb(course: str = '', page: int = 1) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    groups = ['А', 'Ен', 'О', 'К', 'Кс', 'Ц', 'Тм', 'Пр', 'Э', 'И', 'Н', 'Ф', 'П', 'Эк']

    if page == 1:
        for group in groups[:10]:
            builder.button(
                text=group,
                callback_data=f'group_{group}_{course}'
            )
        builder.adjust(2)
        builder.row(
            types.InlineKeyboardButton(text='➡️', callback_data=f'next_page_2_{course}')
        )
        builder.row(
            types.InlineKeyboardButton(text='Вернуться назад', callback_data='prev_crs')
        )
    elif page == 2:
        for group in groups[10:]:
            builder.button(
                text=group,
                callback_data=f'group_{group}_{course}'
            )

        builder.adjust(1)
        builder.row(
            types.InlineKeyboardButton(text='⬅️', callback_data=f'next_page_1_{course}')
        )

    return builder.as_markup()


def get_number_group_kb(group: str, course: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    new_group_number = {
        "Пр": [course + '0', course + '1', course + '2', course + '4'],
        "О": [course + '3', course + '5', course + '6', course + '7', course + '8', course + '9'],
        "Ен": [course + '1'],
        "К": [course + '3', course + '5', course + '7'],
        "Кс": [course + '0', course + '3', course + '4', course + '6'],
        "Тм": [course + '1', course + '2', course + '3', course + '9'],
        "Ц": [course + '1', course + '2'],
        "Э": [course + '1', course + '3', course + '4', course + '5', course + '6', course + '8'],
        "И": [course + '1', course + '2', course + '3', course + '4', course + '5', course + '7'],
        "А": [course + '1', course + '2'],
        "Н": [course + '0', course + '1', course + '2', course + '3', course + '4',
              course + '5', course + '6', course + '7', course + '8'],
        "Ф": [course + '0', course + '2', course + '4', course + '5', course + '6', course + '7'],
        "П": [course + '0', course + '1', course + '2', course + '3', course + '4', course + '5',
              course + '6', course + '8'],
        "Эк": [course + '1']
    }

    buttons = new_group_number.get(group, [])
    current_date = datetime.now().strftime('%d.%m.%Y')
    day_index = datetime.now().isocalendar()[2] - 1
    for button in buttons:
        builder.button(
            text=button,
            callback_data=f"number_{group}-{button}_{day_index}_{current_date}"
        )
    builder.adjust(1)

    builder.row(
        types.InlineKeyboardButton(text='Вернуться назад', callback_data=f'prev_grp_{course}'),
    )
    return builder.as_markup()


def create_navigation_buttons(current_day_index, group_name, current_day):
    buttons = InlineKeyboardBuilder()

    buttons.row(
        types.InlineKeyboardButton(text="⬅️",
                                   callback_data=f"prev_{group_name}_{current_day_index}_{current_day.strftime('%d.%m.%Y')}"),
        types.InlineKeyboardButton(text="➡️",
                                   callback_data=f"next_{group_name}_{current_day_index}_{current_day.strftime('%d.%m.%Y')}")
    )

    buttons.row(
        types.InlineKeyboardButton(text="Сегодня",
                                   callback_data=f"today_{group_name}_{current_day_index}_{current_day.strftime('%d.%m.%Y')}")
    )

    buttons.row(
        types.InlineKeyboardButton(text="Неделя",
                                   callback_data=f"week_{group_name}")
    )

    buttons.row(
        types.InlineKeyboardButton(text="Вернуться назад",
                                   callback_data=f"prev_number_group_{group_name}")
    )
    return buttons.as_markup()


def update_date(action, current_date):
    if action == "prev":
        current_date -= timedelta(days=1)
    elif action == "next":
        current_date += timedelta(days=1)
    elif action == 'today':
        current_date = datetime.now()
    elif action == 'week':


    day_index = current_date.weekday()
    current_week = current_date.isocalendar()[1] + 1
    week_type = "2 нед." if current_week % 2 == 0 else "1 нед."

    return current_date, day_index, week_type


def parse_date(date_str):
    return datetime.strptime(date_str, "%d.%m.%Y")


def format_date_russian(current_date):
    month_cases = {
        "январь": "января", "февраль": "февраля", "март": "марта", "апрель": "апреля",
        "май": "мая", "июнь": "июня", "июль": "июля", "август": "августа",
        "сентябрь": "сентября", "октябрь": "октября", "ноябрь": "ноября", "декабрь": "декабря"
    }

    day = current_date.day
    month_nominative = current_date.strftime("%B").lower()

    month = month_cases.get(month_nominative, month_nominative)

    return f"{day} {month}"


def get_group_schedule(group_name: str, day_index: int, week_type: str, current_date: datetime, user: str):
    day_translation = {
        'monday': 'понедельник', 'tuesday': 'вторник', 'wednesday': 'среда',
        'thursday': 'четверг', 'friday': 'пятница', 'saturday': 'суббота',
        'sunday': 'воскресенье'
    }

    all_schedules = parse_schedule(week_type)

    if group_name not in all_schedules:
        return "Расписание для данной группы не найдено."
    if not isinstance(all_schedules, dict):
        return "Ошибка: расписание не удалось загрузить."

    days_in_order = list(day_translation.values())

    if day_index < 0 or day_index >= len(days_in_order):
        return "Ошибка: некорректный индекс дня недели."

    current_day = days_in_order[day_index]
    next_day = days_in_order[(day_index + 1) % len(days_in_order)]

    group_schedule = all_schedules.get(group_name)

    start_idx = group_schedule[group_schedule['День недели'] == current_day].index
    if start_idx.empty:
        return f"{user}, сегодня воскресенье, иди отдохни;)\n\nНа сегодня расписания нет^^"
    start_idx = start_idx[0]

    end_idx = group_schedule[group_schedule['День недели'] == next_day].index
    end_idx = end_idx[0] if not end_idx.empty else None

    day_schedule = group_schedule.loc[start_idx:end_idx].iloc[:-1] if end_idx else group_schedule.loc[start_idx:]

    if any(day_schedule['Предмет'] == "Выходной"):
        return (f"🗓<b>Расписание {group_name}</b>:\n\n{current_day.capitalize()} | {current_date} | {week_type}\n\n"
                f"<i>Сегодня занятий нет</i>🥰")

    schedule_text = "\n\n".join(
        f"{index + 1}. <b>{row['Предмет']}</b>\n"
        f"    {row['Время']}\n"
        f"    {row['Тип занятия'] if pd.notna(row['Тип занятия']) else ''}, "
        f"ауд. {row['Аудитория'] if pd.notna(row['Аудитория']) else ''}"
        for index, (_, row) in enumerate(day_schedule.iterrows())
        if pd.notna(row['Предмет'])  # Исключаем строки с пустым предметом
    )

    location = [
        row['Расположение'] if pd.notna(row['Расположение']) else '—'
        for _, row in day_schedule.iterrows()
    ]

    if len(location) > 2:
        location_text = location[1]
    elif len(location) == 2:
        location_text = location[-1] if location[0] == '—' else location[0]
    else:
        location_text = location[0]

    return (f"🗓<b>Расписание {group_name}</b>:\n\n{current_day.capitalize()} | {current_date} | "
            f"{week_type}\n\n{schedule_text}\n\n📍<b>Расположение</b>:\n     {location_text}")
