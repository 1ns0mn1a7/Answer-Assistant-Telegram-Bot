import logging
import telegram


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_token, chat_id):
        super().__init__()
        self.bot = telegram.Bot(token=tg_token)
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception:
            pass
