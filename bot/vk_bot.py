import logging
import os
import sys
import time

import telegram
import vk_api
from environs import Env
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from dialogflow_api import detect_intent_texts
from telegram_logger import TelegramLogsHandler


logger = logging.getLogger(__file__)


def send_message(vk, user_id, message):
    try:
        vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            message=message
        )
    except Exception:
        logger.exception(f"Ошибка при отправке сообщения пользователю {user_id}")


def handle_message(vk, user_id, text, project_id):
    try:
        dialogflow_response, is_fallback = detect_intent_texts(project_id, user_id, text)
        if is_fallback:
            return
        send_message(vk, user_id, dialogflow_response)
    except Exception:
        logger.exception(f"Ошибка при обработке сообщения от {user_id}")


def main():
    env = Env()
    env.read_env()

    vk_token = env.str("VK_GROUP_TOKEN")
    project_id = env.str("PROJECT_ID")
    google_credentials = env.str("GOOGLE_APPLICATION_CREDENTIALS")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials
    error_bot_token = env.str("ERROR_BOT_TOKEN")
    error_chat_id = env.int("ERROR_CHAT_ID")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.setLevel(logging.DEBUG)

    telegram.Bot(token=error_bot_token).send_message(chat_id=error_chat_id, text="VK Бот запущен.")
    telegram_handler = TelegramLogsHandler(error_bot_token, error_chat_id)
    telegram_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    telegram_handler.setFormatter(formatter)
    logger.addHandler(telegram_handler)

    logger.info("VK бот запущен.")

    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()

    while True:
        longpoll = VkLongPoll(vk_session)
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    handle_message(vk, event.user_id, event.text, project_id)
        except Exception:
            logger.exception("VK LongPoll упал с ошибкой")
            time.sleep(5)


if __name__ == "__main__":
    main()
