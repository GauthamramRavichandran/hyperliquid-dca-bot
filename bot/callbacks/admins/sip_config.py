from datetime import datetime, timedelta
import json
import logging
import re
from typing import Optional

from humanize import naturaldelta, naturaltime
from hyperliquid.exchange import Exchange
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

from bot.backend import SIPConfigDB
from bot.backend.exceptions import DuplicateLabelError, InsufficientAmountError
from bot.const import (
    STATES, SpotPairMapping, TestnetPairs, confirmation_keyboard
)
from bot.models import HyperliquidManager, Pair


logger = logging.getLogger(__name__)
interval_pattern = re.compile(r"^(\d+)([dhm])$")
from datetime import timedelta
import re



class SipConfig:
    
    @staticmethod
    def parse_interval_to_timedelta(interval: str) -> timedelta:
        """
        Converts an interval string like '1h', '3d', '30m' to a timedelta object.

        Supported suffixes:
            - m: minutes
            - h: hours
            - d: days

        Args:
            interval: A string representing the interval.

        Returns:
            A timedelta object representing the interval.

        Raises:
            ValueError: If the interval format is invalid.
        """
        
        match = interval_pattern.match(interval.lower())
        if match is None:
            raise ValueError("Invalid format")
        num, unit = int(match.group(1)), match.group(2)
        if unit == "d":
            delta = timedelta(days=num)
        elif unit == "h":
            delta = timedelta(hours=num)
        elif unit == "m":
            delta = timedelta(minutes=num)
        else:
            raise ValueError("Invalid unit. Should be one of 'd', 'h', 'm'")
        return delta
    
    @staticmethod
    def calculate_token_amounts(coins: dict[str, float], pairs: list[Pair], sip_amount: float) -> dict[str, dict]:
        """
        Calculate the token amounts for each coin in the SIP strategy.

        :param coins: dict of token -> percentage (0-100)
        :param pairs: list of spot pairs
        :param sip_amount: total USD amount of the SIP
        :return: dict of token -> amount (rounded to 4 decimals)

        Raises ValueError if a price is not found for any of the tokens.
        """
        result: dict[str, dict] = {}

        # Build a lookup for base_token -> price
        price_lookup = {pair.base_token: pair.price for pair in pairs}
        sz_decimals_lookup = {pair.base_token: pair.sz_decimals for pair in pairs}

        for token, percent in coins.items():
            token_usd = sip_amount * (percent / 100)
            price = price_lookup.get(token)
            sz_decimals = sz_decimals_lookup.get(token)

            if price:
                qty = token_usd / price
                result[token] = {"qty":round(qty, sz_decimals), "token_usd": token_usd, "price": price}
            else:
                raise ValueError(f"Price not found for token: {token}")

        return result
    
    @staticmethod
    async def start_add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text("📝 What would you like to name this SIP configuration?")
        return STATES.LABEL

    @staticmethod
    async def received_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
        label = update.effective_message.text
        if label is None or len(label) > 50:
            await update.effective_message.reply_text("❌ Name must be between 1 and 50 characters.")
            return
        sip_config_db: SIPConfigDB = context.bot_data["sip_db"]
        db_record = await sip_config_db.get_config_by_label(label)
        if db_record is not None:
            await update.effective_message.reply_text(f"❌ SIP config with name '{label}' already exists.")
            return
        context.user_data["label"] = label
        await update.message.reply_html("📦 Send the coins composition:"
                                        "\nMake sure it's adding to 100"
                                        "\n\nExamples of valid compositions:"
                                        "\n<code>ETH - 40\nBTC - 60</code>\n"
                                        "\n<code>BTC - 40\nETH - 40\nSOL - 20</code>")
        return STATES.COINS

    @staticmethod
    async def received_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.effective_chat.send_action("typing")
            lines = [line.strip() for line in update.effective_message.text.strip().splitlines()]
            if not lines:
                raise ValueError("Invalid Format")
            coins: dict[str, int] = {}
            for line in lines:
                if "-" not in line:
                    raise ValueError("Invalid Format")
                coin, amount = line.split(" - ")
                amount = int(amount)
                if amount < 0:
                    raise ValueError("Amount cannot be negative")
                if amount > 100:
                    raise ValueError("Amount cannot be greater than 100")
                coins[coin] = amount
            if sum(coins.values()) != 100:
                raise ValueError("Total amount must be 100")
            context.user_data["coins"] = coins
            exchange: Exchange = context.bot_data["exchange"]
            hlm = HyperliquidManager(exchange)
            testnet_pairs_check: bool = context.bot_data["is_mainnet"] == False
            pair_list: list[Pair] = []
            for coin in coins.keys():
                if testnet_pairs_check:
                    if coin not in TestnetPairs:
                        raise ValueError(f"Invalid coin: {coin}\nAvailable testnet coins: {list(TestnetPairs.keys())}")
                    pair: str = TestnetPairs[coin]
                else:
                    # if coin not in SpotPairMapping:
                    #     raise ValueError(f"Invalid coin: {coin}")
                    pair: str = SpotPairMapping.get(coin, coin)
                price: Optional[float] = hlm.get_spot_price(pair)
                pair_list.append(Pair(symbol=pair, price=price, market_type="spot", base_token=coin, quote_token="USDC"))
            context.user_data["pairs"] = pair_list
            pair_list_str = '\n'.join([f'<b>{pair.symbol}</b> (${pair.price:.2f})' for pair in pair_list])
            await update.effective_message.reply_html(f"✅ Coins: \n{(pair_list_str)}") 
            await update.effective_message.reply_html("💰 How much would you like to invest per SIP?\n"
                                                      "\nExample: <code>1000$</code> or <code>500$</code>")
            return STATES.AMOUNT
            
        except ValueError as v:
            logger.exception(v)
            await update.effective_message.reply_html(f"❌ Invalid composition. Please follow the format precisely."
                                                      f"\n<b>Error</b>: {v}")
            return STATES.COINS

    @staticmethod
    async def received_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            sip_amount = int(update.message.text.strip().rstrip("$"))
            context.user_data["amount"] = sip_amount
            coins_breakup_str = ""
            coins_breakup: dict[str, dict] = SipConfig.calculate_token_amounts(context.user_data["coins"], context.user_data["pairs"], sip_amount)
            error = ""
            for coin, attr_dict in coins_breakup.items():
                coins_breakup_str += f'\n<code>{attr_dict["qty"]}</code> <b>{coin}</b> (worth ${attr_dict["token_usd"]:.2f})'
                if attr_dict["qty"] <= 0:
                    error += f'Invalid quantity (<code>{attr_dict["qty"]}</code>) for coin: <b>{coin}</b>\n'
                    coins_breakup_str += '❌'
                elif attr_dict["token_usd"] < 11:
                    error += f'Invalid amount ({attr_dict["token_usd"]}) for coin: <b>{coin}</b>\n'
                    coins_breakup_str += '❌'
                else:
                    coins_breakup_str += '✅'
                    
            await update.effective_message.reply_html(f"🪙 Coins Breakup: \n{(coins_breakup_str)}\n\nEst. coins will be bought every SIP")
            if error:
                raise InsufficientAmountError(f"Error while breaking up the given SIP amount: {error}"
                                                "\nPlease try again with larger SIP amount.")
            
            await update.effective_message.reply_text("⏳ Enter the interval for this SIP:"
                                                      "\nExamples,"
                                                      "\n1d - everyday"
                                                      "\n4h - every 4 hours"
                                                      "\n30m - every 30 minutes"
                                                      "\n\nNote: All intervals are computed in UTC, and starts at 00:00.")
            return STATES.INTERVAL
        except InsufficientAmountError as e:
            await update.effective_message.reply_html(f"{e}")    
            return STATES.AMOUNT
        except ValueError as v:
            await update.effective_message.reply_text("❌ Invalid number. Please enter a valid number without the . or ,")    
            return STATES.AMOUNT
        
    @staticmethod
    async def received_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            interval = update.message.text.strip()
            delta: Optional[timedelta] = SipConfig.parse_interval_to_timedelta(interval)
            
            now = datetime.utcnow()
            start_of_day = datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0)
            next_runs = []
            i = 1
            while len(next_runs) < 5:
                next_run = start_of_day + (i * delta)
                if next_run > now:
                    next_runs.append(next_run)
                i += 1
            context.user_data["interval"] = interval
            
            next_runs_str = ""
            for index, run in enumerate(next_runs, start=1):
                # delta: timedelta = run - datetime.utcnow()
                # minutes = delta.total_seconds() / 60
                next_runs_str += (f"{index}. {run.strftime('%Y-%m-%d %H:%M:%S')} "
                                  f"({naturaltime(run, when=datetime.utcnow())})\n")
                
            await update.effective_message.reply_html(f"✅ <b>Interval</b>: {interval}\n\n"
                                                      f"🕒 Based on the interval you provided, here are the next 5 SIP runs:\n{next_runs_str}")
            await update.effective_chat.send_action("typing")
            coins_breakup: dict[str, dict] = SipConfig.calculate_token_amounts(context.user_data["coins"], 
                                                                               context.user_data["pairs"], 
                                                                               context.user_data["amount"])
            coins_breakup_str = "\n"
            for coin, attr_dict in coins_breakup.items():
                coins_breakup_str += f'\n<code>{attr_dict["qty"]}</code> <b>{coin}</b> (worth ${attr_dict["token_usd"]:.2f})'
            composition_str = " + ".join([f"{qty}% {coin}" for coin, qty in context.user_data["coins"].items()])
            next_immediate_run = naturaltime(next_runs[0], when=datetime.utcnow())
            await update.effective_message.reply_html(f"""
            Review your SIP config,
            
    📛 <b>Name</b>: {context.user_data["label"]}
    🛍 <b>Composition</b>: {composition_str}
    🧮 <b>Coins</b>: {coins_breakup_str}
    
    🕒 <b>Interval</b>: {context.user_data["interval"]}
    💰 <b>Amount</b>: {context.user_data["amount"]}$
    ⏰ <b>Next Immediate Run</b>: <b>{next_runs[0].strftime('%Y-%m-%d %H:%M:%S')} UTC</b> ({next_immediate_run})""")
            await update.effective_message.reply_html(f"⚠️ This is the final confirmation. Bot will start accumulating coins without awaiting any confirmation."
                                                      "\n\nSchedule this SIP now?",
                                                      reply_markup=confirmation_keyboard)
            return STATES.CONFIRMATION
        except ValueError as v:
            logger.exception(v)
            await update.effective_message.reply_html(f"❌ Invalid interval. Please follow the format precisely."
                                                      "\n<b>Error</b>: {v}")
            return STATES.INTERVAL

    
    @staticmethod
    async def received_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        data = update.callback_query.data
        if data != "confirm":
            await update.callback_query.answer("❌ Cancelling SIP config creation.")
            await update.effective_message.reply_text("🚫 SIP config creation cancelled.")
            await update.effective_message.delete()
            context.user_data.clear()
            return ConversationHandler.END
        else:
            await update.callback_query.answer("✅ Confirming SIP config...")
            await update.effective_message.delete()
        sip_config_db: SIPConfigDB = context.bot_data["sip_db"]
        try:
            await sip_config_db.add_config(
                label=context.user_data["label"],
                coins=context.user_data["coins"],
                interval=context.user_data["interval"],
                amount=context.user_data["amount"],
            )
            await update.effective_message.reply_text("✅ SIP config added successfully.")
        except DuplicateLabelError as e:
            await update.effective_message.reply_text(f"⚠️ {e}")
        except Exception as e:
            await update.effective_message.reply_text("❌ Unexpected error occurred.")
            context.user_data.clear()
            raise e
        context.user_data.clear()
        return ConversationHandler.END

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text("🚫 SIP config creation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
