from dotenv import load_dotenv
load_dotenv()  # Эта строчка сама найдет файл .env и загрузит ключи
import asyncio
import logging
import os
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токены и доступы. Локально для тестов можешь временно вставить строки вместо os.getenv
BOT_TOKEN = os.getenv("BOT_TOKEN", "СЮДА_ВСТАВЬ_ТОКЕН_ДЛЯ_ТЕСТА")
DATABASE_URL = os.getenv("DATABASE_URL", "СЮДА_ВСТАВЬ_ССЫЛКУ_НА_БД_СУПАБЕЙС")

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


async def main():
    print("🚀 Бот запущен на общей СУБД Supabase...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())