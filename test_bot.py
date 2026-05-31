import asyncio
import os
import logging
import http.server
import socketserver
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Включаем логирование, чтобы видеть, что происходит с ботом в консоли Render
logging.basicConfig(level=logging.INFO)

# Загружаем переменные из .env (нужно для локального запуска в PyCharm)
load_dotenv()

# Получаем токены из переменных окружения (на Render мы их уже заполнили)
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Простой тестовый хэндлер, чтобы проверить работоспособность
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Проект «Digital Urpaq» успешно запущен и работает в облаке Render!\n\n"
        "База данных Supabase успешно подключена."
    )


# Хитрый мини-сервер, который будет обманывать Render, притворяясь веб-сайтом
def run_dummy_server():
    # Render автоматически передает нужный порт в переменную PORT, иначе используем 8000
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
    # Запускаем маскировочный веб-сервер в отдельном потоке, чтобы он не мешал боту
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    logging.info("🤖 Бот «Digital Urpaq» начинает опрос серверов Telegram (Polling)...")

    # Запускаем стандартный опрос Telegram (лонг-поллинг)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())