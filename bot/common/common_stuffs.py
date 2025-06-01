from telegram.ext import ContextTypes


async def inform_admin(context: ContextTypes.DEFAULT_TYPE, message: str, parse_mode=None) -> None:
    await context.bot.send_message(chat_id=context.bot_data["admin_id"], text=message, parse_mode=parse_mode)