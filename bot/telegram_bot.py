import os
import sys
import logging
from environs import Env
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from google.cloud import dialogflow_v2 as dialogflow


logger = logging.getLogger(__file__)


class DialogFlowBot:
    def __init__(self):
        try:
            env = Env()
            env.read_env()

            self.telegram_token = env.str("TELEGRAM_BOT_TOKEN")
            self.project_id = env.str("PROJECT_ID")
            google_credentials = env.str("GOOGLE_APPLICATION_CREDENTIALS")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials

            self.updater = Updater(self.telegram_token, use_context=True)
            dp = self.updater.dispatcher

            dp.add_handler(CommandHandler("start", self.start))
            dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))

        except (KeyError, ValueError) as error:
            logger.error(f"Ошибка при инициализации бота: {error}")
            raise

        except Exception as error:
            logger.error(f"Неизвестная ошибка при инициализации бота: {error}")
            raise

    def detect_intent_texts(self, session_id, text, language_code='ru'):
        try:
            session_client = dialogflow.SessionsClient()
            session = session_client.session_path(self.project_id, session_id)
            text_input = dialogflow.TextInput(text=text, language_code=language_code)
            query_input = dialogflow.QueryInput(text=text_input)
            response = session_client.detect_intent(session=session, query_input=query_input)
            return response.query_result.fulfillment_text

        except Exception as error:
            logger.error(f"Ошибка при обработке запроса Dialogflow: {error}")
            return None

    def start(self, update, context):
        try:
            update.message.reply_text("Здравствуйте! Напишите что-нибудь.")
            
        except Exception as error:
            logger.error(f"Ошибка при обработке команды /start: {error}")
            update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

    def handle_message(self, update, context):
        user_text = update.message.text
        session_id = update.message.chat_id
        try:
            dialogflow_response = self.detect_intent_texts(session_id, user_text)
            update.message.reply_text(dialogflow_response if dialogflow_response else "Я вас не понял.")

        except Exception as error:
            logger.error(f"Ошибка при получении сообщения: {error}")

    def run(self):
        try:
            logger.info("Бот запущен.")
            self.updater.start_polling()
            self.updater.idle()

        except Exception as error:
            logger.error(f"Ошибка при запуске бота: {error}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.setLevel(logging.DEBUG)
    bot = DialogFlowBot()
    bot.run()
