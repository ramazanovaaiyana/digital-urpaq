import asyncio
import logging
import os
import asyncpg
import http.server
import socketserver
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Эта строчка сама найдет файл .env и загрузит ключи (нужно для локальных тестов)
load_dotenv()

# Токены и доступы (на Render они автоматически берутся из настроек Environment)
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Добро пожаловать в бот портала <b>«Digital Urpaq»</b>.\n\n"
        "Чтобы связать этот чат со своим аккаунтом на сайте, введи команду:\n"
        "<code>/link ТВОЙ_КОД</code>\n\n"
        "<i>Например: /link 778899</i>",
        parse_mode="HTML"
    )


@dp.message(Command("link"))
async def cmd_link(message: types.Message):
    args = message.text.split()

    if len(args) < 2:
        await message.answer(
            "❌ Ошибка! Передай код из личного кабинета.\nПример: <code>/link 778899</code>",
            parse_mode="HTML"
        )
        return

    user_code = args[1]
    chat_id = message.chat.id

    try:
        # Подключаемся к Supabase PostgreSQL друга
        conn = await asyncpg.connect(DATABASE_URL)

        # Выполняем SQL-запрос обновления
        result = await conn.execute(
            "UPDATE users SET telegram_chat_id = $1, telegram_code = NULL WHERE telegram_code = $2",
            chat_id, user_code
        )

        await conn.close()

        if result != "UPDATE 0":
            await message.answer(
                "🎉 <b>Успешно привязано!</b>\n\n"
                "Ваш Telegram привязан к личному кабинету. "
                "Когда администратор рассмотрит вашу заявку, вы получите пуш-уведомление сюда.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ <b>Ошибка привязки!</b>\n\n"
                "Этот код не найден в системе Supabase или уже устарел.",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"Ошибка БД: {e}")
        await message.answer("💥 Произошла ошибка при подключении к базе данных.")


# Хитрый мини-сервер, который будет обманывать Render, притворяясь веб-сайтом
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
    # Запускаем маскировочный веб-сервер в отдельном потоке, чтобы он не мешал боту опроса
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    logging.info("🚀 Бот запущен на общей СУБД Supabase и слушает сервера Telegram...")

    # Запускаем стандартный опрос Telegram (лонг-поллинг)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())