import os
import sys
import logging
from environs import Env
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from google.cloud import dialogflow_v2 as dialogflow


logger = logging.getLogger(__file__)


class VkDialogFlowBot:
    def __init__(self):
        try:
            env = Env()
            env.read_env()

            self.vk_token = env.str("VK_GROUP_TOKEN")
            self.project_id = env.str("PROJECT_ID")
            google_credentials = env.str("GOOGLE_APPLICATION_CREDENTIALS")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials

            self.vk_session = vk_api.VkApi(token=self.vk_token)
            self.vk = self.vk_session.get_api()
            self.longpoll = VkLongPoll(self.vk_session)

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

    def send_message(self, user_id, message):
        try:
            self.vk.messages.send(
                user_id=user_id,
                random_id=get_random_id(),
                message=message
            )
        except Exception as error:
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {error}")

    def handle_message(self, user_id, text):
        try:
            dialogflow_response = self.detect_intent_texts(user_id, text)
            reply_text = dialogflow_response if dialogflow_response else "Я вас не понял."
            self.send_message(user_id, reply_text)
        except Exception as error:
            logger.error(f"Ошибка при обработке сообщения от {user_id}: {error}")

    def run(self):
        try:
            logger.info("VK бот запущен.")
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_message(event.user_id, event.text)
        except Exception as error:
            logger.error(f"Ошибка при запуске бота: {error}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    bot = VkDialogFlowBot()
    bot.run()
