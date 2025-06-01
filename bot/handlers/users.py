from telegram.ext import CommandHandler

from bot.callbacks import UserMisc

class Users:
    start_handler = CommandHandler("start", UserMisc.start)
    
    def __call__(self) -> list:
        return [self.start_handler]
