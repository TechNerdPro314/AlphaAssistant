# bot.py
import os
import requests
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Загружаем переменные окружения
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования для отладки
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TELEGRAM_TOKEN:
    TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip("\"'")

API_BASE_URL = "http://127.0.0.1:5000/api/v1"

user_sessions = {}


async def login_user(email, password):
    """Отправляет запрос на логин в наше API и возвращает JWT токен."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login", json={"email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        logger.error(f"API Login failed: {e}")
        return None


async def link_telegram_account(token, telegram_id):
    """Привязывает telegram_id к аккаунту пользователя в нашем API."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{API_BASE_URL}/profile/link_telegram",
            headers=headers,
            json={"telegram_id": str(telegram_id)},
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"API Link Telegram failed: {e}")
        return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Привет, {user.mention_html()}!\n\n"
        "Я твой бизнес-ассистент. Чтобы начать, войди в свой аккаунт.\n\n"
        "Используй команду: `/login email@example.com ваш_пароль`\n\n"
        "⚠️ В целях безопасности я удалю твое сообщение с паролем сразу после отправки."
    )


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /login."""
    chat_id = update.effective_chat.id

    try:
        await context.bot.delete_message(
            chat_id=chat_id, message_id=update.message.message_id
        )
    except Exception as e:
        logger.warning(f"Could not delete login message: {e}")

    if len(context.args) != 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Неверный формат. Используй: `/login <email> <password>`",
        )
        return

    email, password = context.args
    await context.bot.send_message(chat_id=chat_id, text="Проверяю данные...")

    token = await login_user(email, password)
    if not token:
        await context.bot.send_message(
            chat_id=chat_id, text="❌ Ошибка входа. Проверь свой email и пароль."
        )
        return

    telegram_id = update.effective_user.id
    if not await link_telegram_account(token, telegram_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Не удалось привязать аккаунт Telegram. Попробуй позже.",
        )
        return

    user_sessions[telegram_id] = {"jwt_token": token, "session_id": None}
    await context.bot.send_message(
        chat_id=chat_id,
        text="✅ Вход выполнен успешно! Теперь можешь задавать мне вопросы.",
    )


async def new_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    if telegram_id in user_sessions:
        user_sessions[telegram_id]["session_id"] = None
        await update.message.reply_text(
            "Новый диалог начат. Контекст предыдущего сброшен."
        )
    else:
        await update.message.reply_text("Сначала войдите в систему с помощью /login.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    text = update.message.text

    # Проверяем, залогинен ли пользователь
    if telegram_id not in user_sessions:
        await update.message.reply_text(
            "Пожалуйста, сначала войдите в систему с помощью команды /login."
        )
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    session_data = user_sessions[telegram_id]
    token = session_data["jwt_token"]
    chat_session_id = session_data.get("session_id")

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message_content": text, "model": "gigachat"}

    if chat_session_id is not None:
        payload["session_id"] = chat_session_id

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/send_message", headers=headers, json=payload
        )

        if response.status_code == 401:
            await update.message.reply_text(
                "Ваша сессия истекла. Пожалуйста, войдите снова: /login <email> <password>"
            )
            del user_sessions[telegram_id]
            return

        response.raise_for_status()

        data = response.json()
        assistant_message = data["assistant_message"]["content"]
        new_session_id = data["session_id"]

        user_sessions[telegram_id]["session_id"] = new_session_id

        await update.message.reply_text(assistant_message)

    except requests.exceptions.RequestException as e:
        logger.error(f"API Error during send_message: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обращении к ассистенту. Попробуйте еще раз."
        )


bot_application = None


async def stop_bot():
    global bot_application
    if bot_application:
        await bot_application.stop()


def main():
    global bot_application

    if not TELEGRAM_TOKEN:
        logger.error("Не найден TELEGRAM_BOT_TOKEN! Проверьте файл .env")
        return

    logger.info(
        f"TELEGRAM_BOT_TOKEN found with length: {len(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else 0}"
    )

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    bot_application = application

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("new", new_chat_command))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Запускаем бота
    logger.info("Starting bot...")
    application.run_polling(stop_signals=[])


if __name__ == "__main__":
    main()
