from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler)

from bot.callbacks import SipConfig
from bot.const import (
    STATES
)

class Admins: 
    add_sip_config = ConversationHandler(
            entry_points=[CommandHandler("add_config", SipConfig.start_add_config)],
            states={
                STATES.LABEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, SipConfig.received_label)],
                STATES.COINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, SipConfig.received_coins)],
                STATES.AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, SipConfig.received_amount)],
                STATES.INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, SipConfig.received_interval)],
                STATES.CONFIRMATION: [CallbackQueryHandler(SipConfig.received_confirmation, pattern="^confirm$|^cancel$")],
            },
            fallbacks=[CommandHandler("cancel", SipConfig.cancel)],
        )
    
    def __call__(self) -> list:
        return [self.add_sip_config]


