import asyncio
import logging
import os
from pathlib import Path

from telegram.ext import Application, ApplicationBuilder, ContextTypes
from telegram import Update

from bot.backend import InternalConfigDB, SIPConfigDB
from bot.backend.db_utils import init_db
from bot.handlers import Users, Admins
from bot.models.config_manager import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def load_config(app: Application):
    try:
        config_manager = ConfigManager(Path("config.yaml"))
        await config_manager.validate()
        config = config_manager.config
        app.bot_data["config"] = config
        logger.info("✅ Config validated successfully.")
        
        db_path = config_manager.get_db_path()
        init_db(db_path)
        logger.info("✅ DB initialized successfully.")
        
        app.bot_data["sip_db"] = SIPConfigDB(db_path)
        app.bot_data["internal_db"] = InternalConfigDB(db_path)
        
        # store instantiated hyperliquid exchange
        app.bot_data["exchange"] = config_manager.exchange
        app.bot_data["is_mainnet"] = config_manager.is_mainnet
    except Exception as e:
        logger.exception(f"❌ Config validation failed: {e}")
        raise


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
    handlers = Users()() + Admins()()
    for handler in handlers:
        application.add_handler(handler)
    logger.info("Starting the bot...")
    application.run_polling()


if __name__ == "__main__":
    main()
