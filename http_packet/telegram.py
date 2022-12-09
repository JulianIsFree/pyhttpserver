import telebot


class Bot(telebot.TeleBot):
    def __init__(self, token: str):
        super().__init__(token)

