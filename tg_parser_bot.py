import telebot
from telebot import types
import os
from dotenv import load_dotenv
from utils import find_area_id, get_skills, areas

# Загружаем переменные окружения из файла .env, инициализируем бота
load_dotenv()
TG_TOKEN = os.getenv('TG_TOKEN')
bot = telebot.TeleBot(TG_TOKEN)

# Хранилище данных пользователей
user_data = {}

# Список графиков работы
schedule_mapping = {
    "Полный день": "fullDay",
    "Сменный график": "shift",
    "Удалённая работа": "remote",
    "Гибкий график": "flexible"
}

# Настройка списка команд для меню
bot.set_my_commands([
    telebot.types.BotCommand("start", "Запустить бота"),
    telebot.types.BotCommand("help", "Получить помощь")
])

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "Доступные команды:\n"
        "/start - Запустить бота и начать поиск вакансий\n"
        "/help - Получить помощь по использованию бота\n\n"
        "Сначала отправьте команду /start, чтобы бот начал последовательный запрос параметров для поиска."
    )
    bot.send_message(message.chat.id, help_text)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот-парсер Head Hunter.\n\nУкажи, пожалуйста, регион для поиска вакансий.")
    user_data[message.chat.id] = {}  # Инициализация данных пользователя

# Получение региона
@bot.message_handler(func=lambda message: message.chat.id in user_data and 'region' not in user_data[message.chat.id])
def get_region(message):
    try:
        region_name = message.text.strip()
        area_id = find_area_id(region_name, areas)
        user_data[message.chat.id]['region'] = area_id
        user_data[message.chat.id]['region_name'] = region_name  # Сохранение названия региона
        bot.send_message(message.chat.id, "Отлично! Теперь укажи название специальности (например: Python Developer).")
    except ValueError as e:
        bot.send_message(message.chat.id, str(e))

# Получение специальности
@bot.message_handler(func=lambda message: message.chat.id in user_data and 'region' in user_data[message.chat.id] and 'specialty' not in user_data[message.chat.id])
def get_specialty(message):
    specialty = message.text.strip()
    user_data[message.chat.id]['specialty'] = specialty

    # Отправляем клавиатуру для выбора графика работы
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for name, value in schedule_mapping.items():
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data=f"schedule_{value}"))
    bot.send_message(message.chat.id, "Выбери тип занятости:", reply_markup=keyboard)

# Обработка выбора графика работы
@bot.callback_query_handler(func=lambda call: call.data.startswith("schedule_"))
def select_schedule(call):
    schedule = call.data.split("_")[1]
    user_data[call.message.chat.id]["schedule"] = schedule

    # Отправляем сообщение о запуске поиска
    bot.send_message(call.message.chat.id, "Выполняется поиск, пожалуйста, подождите...")

    # Подготовка данных для запроса
    region_id = user_data[call.message.chat.id]['region']
    region_name = user_data[call.message.chat.id]['region_name']
    specialty = user_data[call.message.chat.id]['specialty']

    # Подготовка параметров для запроса
    params = {
        'text': specialty,
        'area': region_id,
        'schedule': schedule
    }

    # Запуск парсинга
    skills, total_vacancies = get_skills(params)

    # Сортировка и отбор топ-10 навыков
    sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:20]

    # Формирование ответа
    response = f"Результаты для вакансии '{specialty}'\nВ регионе: {region_name}\n\n"
    response += f"Всего найдено вакансий: {total_vacancies}\n\nТоп навыков:\n"
    for skill, percentage in sorted_skills:
        response += f"- {skill}: {percentage}%\n"

    bot.send_message(call.message.chat.id, response)
    user_data.pop(call.message.chat.id)  # Очистка данных после завершения

bot.polling(none_stop=True)
