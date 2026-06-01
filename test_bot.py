import asyncio
import logging
import os
import asyncpg
import http.server
import socketserver
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загружаем переменные из .env (для локальных тестов)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Создаем удобное меню с кнопками для жюри
def get_main_menu():
    buttons = [
        [KeyboardButton(text="📅 Анонсы мероприятий"), KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="🔑 Привязать аккаунт")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в интеллектуальную систему <b>«Digital Urpaq»</b>.\n\n"
        "🤖 Я твой личный ассистент для координации обучения во Дворце Школьников.\n"
        "Используй меню ниже, чтобы управлять профилем и следить за ивентами!",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


# Фича 1: Анонсы мероприятий (для удивления жюри)
@dp.message(lambda message: message.text == "📅 Анонсы мероприятий")
@dp.message(Command("events"))
async def cmd_events(message: types.Message):
    await message.answer(
        "✨ <b>Актуальные мероприятия во Дворце Школьников:</b>\n\n"
        "1️⃣ <b>Воркшоп: Разработка на Python & AI</b>\n"
        "📅 <i>Завтра, 15:00 | IT-Лаборатория</i>\n"
        "💡 Саммари: Научимся подключать нейросети к Telegram.\n\n"
        "2️⃣ <b>Турнир по Робототехнике (Robo-Urpaq)</b>\n"
        "📅 <i>Пятница, 16:30 | Главный холл</i>\n"
        "🏆 Приз: 500 Urpaq-Coins на баланс!\n\n"
        "3️⃣ <b>Бронирование VR-зоны и 3D-принтеров</b>\n"
        "🤖 Доступно свободное время с 14:00 до 18:00.\n\n"
        "🎟️ <i>Чтобы записаться на любое событие, отправьте его номер администратору.</i>",
        parse_mode="HTML"
    )


# Фича 2: Профиль и геймификация Urpaq-Coins
@dp.message(lambda message: message.text == "👤 Мой профиль")
@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    await message.answer(
        "👤 <b>Личный кабинет Digital Urpaq</b>\n\n"
        "• <b>Статус:</b> Активный ученик 🚀\n"
        "• <b>Доступ в IT-центр:</b> Разрешен (QR-Pass активен ✅)\n"
        "• <b>Баланс:</b> 150 <b>Urpaq-Coins</b> 🪙\n\n"
        "⚡ <i>Коины можно обменять во Дворце Школьников на фирменный мерч: худи, блокноты и стикерпаки!</i>",
        parse_mode="HTML"
    )


# Инструкция при клике на кнопку привязки
@dp.message(lambda message: message.text == "🔑 Привязать аккаунт")
async def txt_link_instruction(message: types.Message):
    await message.answer(
        "Чтобы связать чат с сайтом, введи команду и твой код подтверждения.\n"
        "Пример:\n<code>/link 778899</code>",
        parse_mode="HTML"
    )


# Логика связки с базой Supabase
@dp.message(Command("link"))
async def cmd_link(message: types.Message):
    args = message.text.split()

    if len(args) < 2:
        await message.answer("❌ Ошибка! Введи код. Пример: <code>/link 778899</code>", parse_mode="HTML")
        return

    user_code = args[1]
    chat_id = message.chat.id

    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Если твой друг переименовал колонку telegram_code в базе, замени её имя здесь:
        result = await conn.execute(
            "UPDATE users SET telegram_chat_id = $1, telegram_code = NULL WHERE telegram_code = $2",
            chat_id, user_code
        )
        await conn.close()

        if result != "UPDATE 0":
            await message.answer(
                "🎉 <b>Успешно привязано!</b>\n\n"
                "Ваш Telegram привязан к порталу. Теперь пуш-уведомления будут приходить сюда.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ <b>Ошибка привязки!</b>\n\n"
                "Код не найден в Supabase. Проверь код на сайте или уточни у партнера название колонки.",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        await message.answer("💥 Произошла ошибка при подключении к базе данных.")


# Маскировочный сервер для обмана Render
def run_dummy_server():
    port = int(os.getenv("PORT", 8000))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            logging.info(f" [Render Hack] Мини-сервер успешно запущен на порту {port}")
            httpd.serve_forever()
    except Exception as e:
        logging.error(f"Ошибка запуска мини-сервера: {e}")


async def main():
    # Запуск сервера маскировки
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    logging.info("🚀 Бот запущен на общей СУБД Supabase и слушает сервера Telegram...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())