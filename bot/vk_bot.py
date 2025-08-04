import random

import os
from environs import Env
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id


env = Env()
env.read_env()

VK_GROUP_TOKEN = env.str("VK_GROUP_TOKEN")

vk_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)


def send_message(user_id, message):
    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        message=message
    )


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        print(f"Новое сообщение от {event.user_id}: {event.text}")
        send_message(event.user_id, event.text)
