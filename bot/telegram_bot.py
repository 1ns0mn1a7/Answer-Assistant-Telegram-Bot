import logging
import os
import sys
import time

from environs import Env
from telegram import Bot
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from dialogflow_api import detect_intent_texts
from telegram_logger import TelegramLogsHandler


logger = logging.getLogger(__file__)


def start(update, context):
    try:
        update.message.reply_text("Здравствуйте! Чем могу помочь?")
    except Exception:
        logger.exception("Ошибка при обработке команды /start")
        update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")


def handle_message(update, context):
    user_text = update.message.text
    session_id = update.message.chat_id
    project_id = context.bot_data["project_id"]
    try:
        dialogflow_response, _ = detect_intent_texts(project_id, session_id, user_text)
        update.message.reply_text(dialogflow_response if dialogflow_response else "Я вас не понял.")
    except Exception:
        logger.exception("Ошибка при получении сообщения")


def main():
    env = Env()
    env.read_env()

    project_id = env.str("PROJECT_ID")
    google_credentials = env.str("GOOGLE_APPLICATION_CREDENTIALS")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials
    telegram_token = env.str("TELEGRAM_BOT_TOKEN")
    error_bot_token = env.str("ERROR_BOT_TOKEN")
    error_chat_id = env.int("ERROR_CHAT_ID")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.setLevel(logging.DEBUG)

    error_bot = Bot(token=error_bot_token)
    telegram_handler = TelegramLogsHandler(error_bot_token, error_chat_id)
    telegram_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    telegram_handler.setFormatter(formatter)
    logger.addHandler(telegram_handler)

    error_bot.send_message(chat_id=error_chat_id, text="Telegram Бот запущен.")
    logger.info("Telegram Бот запущен.")

    updater = Updater(telegram_token, use_context=True)
    dp = updater.dispatcher
    dp.bot_data["project_id"] = project_id
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    while True:
        try:
            updater.start_polling()
            updater.idle()
        except Exception:
            logger.exception("Telegram Бот упал с ошибкой")
            time.sleep(5)


if __name__ == "__main__":
    main()
