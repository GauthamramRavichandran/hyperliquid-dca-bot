from telegram import InlineKeyboardButton, InlineKeyboardMarkup

confirmation_keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ]
    ]
)