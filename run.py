import asyncio
import logging
from pathlib import Path

from telegram.ext import Application, ApplicationBuilder, ContextTypes
from telegram import Update

from bot.handlers import Users
from bot.models.config_manager import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

async def load_config(application: Application):
    try:
        config_manager = ConfigManager(Path("config.yaml"))
        await config_manager.validate()
        config = config_manager.config
        application.bot_data["config"] = config
        logger.info("✅ Config validated successfully.")
    except Exception as e:
        logger.exception(f"❌ Config validation failed: {e}")
        return

def main():
    # Load the config for getting the bot token of Telegram
    config_manager = ConfigManager(Path("config.yaml"))
    config_manager.load_config_file()
    config = config_manager.config
    print(config)
    application = (
        ApplicationBuilder()
        .token(config["telegram"]["bot_token"])
        .post_init(load_config)
        .build()
    )
    handlers = Users()()
    for handler in handlers:
        application.add_handler(handler)
    logger.info("Starting the bot...")
    application.run_polling()


if __name__ == "__main__":
    main()
