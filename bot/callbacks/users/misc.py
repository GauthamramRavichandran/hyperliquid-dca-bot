from telegram import Update
from telegram.ext import CallbackContext

class UserMisc:
    @staticmethod
    async def start(update: Update, context:CallbackContext):
        await update.effective_message.reply_text("Hello!")