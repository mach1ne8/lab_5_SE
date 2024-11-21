from aiogram import F
import locale
import logging
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode
from db import save_user, create_db_pool, get_user_questions, save_question, get_message_count
# from aiogram import Bot
# from config import TOKEN_BOT
from main import bot
from handlers.pattern_base import (get_course_kb, get_group_kb, get_number_group_kb, get_group_schedule, update_date,
                                   parse_date, create_navigation_buttons, format_date_russian)

router = Router()
# bot = Bot(token=TOKEN_BOT)
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

ADMIN_CHAT_ID = '7869744858'


@router.message(Command("start"))
async def cmd_start(message: Message):
    pool = await create_db_pool()

    await save_user(pool, message.from_user)

    await pool.close()

    await message.answer(
        f"Привет, {message.from_user.full_name}!\n\nДобро пожаловать в бота с расписанием, который будет всегда"
        f" под рукой во всеми нами любимом телеграме:)\n\nКоманды:\n/start - выведет сообщение, которое ты читаешь"
        f" сейчас\n/timetable - переход к просмотру расписания\n/support - можете написать свой вопрос или предложение"
        f" по работе бота"
    )


@router.message(Command('timetable'))
async def cmd_course(message: types.Message):
    await message.answer(
        "Выберите ваш курс:",
        reply_markup=get_course_kb()
    )


@router.callback_query(F.data.startswith("course_"))
async def process_course_callback(callback_query: types.CallbackQuery):
    course = callback_query.data.split("_")[1]

    await callback_query.message.edit_text(
        "Выберите вашу группу:",
        reply_markup=get_group_kb(course)
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("prev_crs"))
async def process_prev_page_callback(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "Выберите ваш курс:",
        reply_markup=get_course_kb()
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("prev_grp"))
async def process_prev_page_callback(callback_query: types.CallbackQuery):
    course = callback_query.data.split("_")[2]

    await callback_query.message.edit_text(
        "Выберите вашу группу:",
        reply_markup=get_group_kb(course)
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith('next_page_'))
async def process_next_page_callback(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[2])
    course = callback_query.data.split('_')[3]

    await callback_query.message.edit_text(
        "Выберите вашу группу",
        reply_markup=get_group_kb(course, page)
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("prev_page_"))
async def process_prev_page_callback(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split('_')[2])
    course = callback_query.data.split('_')[3]

    await callback_query.message.edit_text(
        "Выберите вашу группу:",
        reply_markup=get_group_kb(course, page)
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith('group_'))
async def process_group_callback(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split('_')
    group = data_parts[1]
    course = data_parts[2]

    await callback_query.message.edit_text(
        f'Выберите номер группы:',
        reply_markup=get_number_group_kb(group, course)
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("prev_number_group_"))
async def process_prev_page_callback(callback_query: types.CallbackQuery):
    group = callback_query.data.split('_')[3][0]
    course = callback_query.data.split('_')[3][2]

    await callback_query.message.edit_text(
        "Выберите номер группы:",
        reply_markup=get_number_group_kb(group, course)
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith(("number_", "prev_", "next_", "today_", "week_")))
async def process_group_callback(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split('_')

    action = data_parts[0]
    group_name = data_parts[1]
    user = callback_query.from_user.full_name
    try:
        current_date = parse_date(data_parts[3])  # Преобразуем строку в объект datetime
    except (ValueError, IndexError) as e:
        await callback_query.answer("Ошибка: Некорректные данные.")
        print(f"Ошибка: Некорректные данные в callback_data: {callback_query.data}")
        return

    current_date, day_index, week_type = update_date(action, current_date)
    formatted_date = format_date_russian(current_date)

    schedule_text = get_group_schedule(group_name, day_index, week_type, formatted_date, user)

    current_message_text = callback_query.message.html_text

    if action == "today" and schedule_text == current_message_text:
        await callback_query.answer("Это текущий день", show_alert=False)
        return

    await callback_query.message.edit_text(
        schedule_text,
        reply_markup=create_navigation_buttons(day_index, group_name, current_date),
        parse_mode=ParseMode.HTML
    )

    await callback_query.answer()


class QuestionForm(StatesGroup):
    waiting_for_question = State()


@router.message(Command('support'))
async def help_command(message: Message, state: FSMContext):
    if str(message.from_user.id) == ADMIN_CHAT_ID:
        await message.answer("Эта команда доступна только пользователям")
        return

    await message.answer("Задайте ваш вопрос:")
    await state.set_state(QuestionForm.waiting_for_question)


@router.message(QuestionForm.waiting_for_question)
async def handle_question(message: Message, pool, state: FSMContext):
    question_text = message.text
    await state.clear()

    if pool is None:
        logging.error("Пул базы данных не был инициализирован.")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
        return

    await save_question(
        pool,
        user_id=message.from_user.id,
        message_id=message.message_id,
        question_text=question_text,
        username=message.from_user.username or "unknown"
    )

    message_count = await get_message_count(pool, message.from_user.id)

    await bot.send_message(
        ADMIN_CHAT_ID,
        f"Новый вопрос от {message.from_user.full_name} "
        f"(@{message.from_user.username or 'unknown'}, ID: {message.from_user.id}):\n"
        f"{question_text}\n\n"
        f"Количество сообщений от пользователя: {message_count}\n"
        f"Чтобы ответить, используйте команду: /reply {message.from_user.id} <индекс вопроса> <ответ>"
    )

    await message.answer("Ваш вопрос отправлен администратору. Ожидайте ответа!")


@router.message(Command("reply"))
async def reply_to_user(message: Message, pool):
    if str(message.from_user.id) != ADMIN_CHAT_ID:
        await message.answer("Эта команда доступна только администратору")
        return

    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("Используйте команду в формате /reply <user_id> <индекс вопроса> <ответ>")
        return

    user_id = int(parts[1])
    question_index = int(parts[2])
    reply_text = parts[3]

    if pool is None:
        logging.error("Пул базы данных не был инициализирован.")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
        return

    try:
        questions = await get_user_questions(pool, user_id)
    except Exception as e:
        logging.error(f"Ошибка при получении вопросов для пользователя {user_id}: {e}")
        await message.answer("Произошла ошибка при получении данных из базы.")
        return

    if question_index < 0 or question_index >= len(questions):
        await message.answer("Не найдено вопросов с указанным индексом для этого пользователя.")
        return

    question_message_id = questions[question_index]["message_id"]

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"Ответ от администратора:\n\n{reply_text}",
            reply_to_message_id=question_message_id
        )
        await message.answer(f"Ответ на вопрос #{question_index} отправлен пользователю.")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        await message.answer("Не удалось отправить сообщение. Проверьте корректность данных.")
