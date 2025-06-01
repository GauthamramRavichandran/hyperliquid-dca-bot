import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import yaml
import re
from typing import Dict, Any, Optional, Union

from eth_account import Account
from eth_utils import is_checksum_address
from eth_utils.exceptions import ValidationError
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants, error
from telegram import Bot, Chat
from telegram.error import TelegramError

from ..backend.db_utils import init_db
from ..backend.internal_config import InternalConfig
from ..models.hyperliquid_manager import HyperliquidManager

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass

class ConfigManager:
    def __init__(self, config_path: Path) -> None:
        """
        Initialize the ConfigManager.

        Args:
            config_path: Path to the configuration YAML file.
        """
        self.config_path: Path = config_path
        self.config: Dict[str, Any] = {}
        self.config_hash: str = ""
        self.exchange: Optional[Exchange] = None
        self.is_mainnet: bool = False
        
    def load_config_file(self) -> None:
        """
        Load the configuration from the config YAML file.

        This method will load the configuration from the YAML file and store it in the `config` attribute.
        """
        if not self.config_path.exists():
            raise ConfigError(f"Config file '{self.config_path}' not found. Please create it before running the bot.")
        with open(self.config_path, "r") as f:
            print("Read config file")
            self.config = yaml.safe_load(f) or {}
    
    def get_db_path(self) -> str:
        """
        Determine the database path based on the current configuration.

        This method creates a 'data' directory if it does not exist and returns the path to the
        database file. The path is determined by whether the application is configured to use
        the testnet or mainnet.

        Returns:
            str: The file path to the database, either 'data/testnet.db' or 'data/mainnet.db'.
        """

        db_folder = "data"
        os.makedirs(db_folder, exist_ok=True)
        
        if self.config["hyperliquid"]["testnet"]:
            db_path = os.path.join(db_folder, "testnet.db")
        else:
            db_path = os.path.join(db_folder, "mainnet.db")
            self.is_mainnet = True
            
        init_db(db_path)
        return db_path
    
    async def load_config(self) -> bool:
        """
        Load the configuration from the config YAML file.

        This method will load the configuration from the YAML file and store it in the `config` attribute.
        It will also compute the SHA-256 hash of the configuration and store it in the `config_hash` attribute.
        The method will return `True` if the configuration has been changed since the last successful run, and `False` otherwise.

        Raises:
            ConfigError: If the configuration file does not exist.
        """
        self.load_config_file()

        # Compute the SHA-256 hash of the configuration
        self.config_hash: str = hashlib.sha256(json.dumps(self.config).encode()).hexdigest()
        db_path = self.get_db_path()
        # Check if the configuration has been changed since the last successful run
        last_success_hash = await InternalConfig(db_path).get("config_hash")
        if last_success_hash == self.config_hash:
            return False
        return True

    def initial_validation(self) -> None:
        """
        Perform initial validation of the configuration.

        Checks for the following:
            * `telegram.bot_token` is a string in the format of `<integer>:<string-35-chars>`
            * `telegram.user_id` is an integer
            * `hyperliquid.wallet_address` is a non-empty string
            * `hyperliquid.private_key` is a non-empty string

        Raises:
            ConfigError: If any of the above checks fail.
        """
        errors: list[str] = []

        telegram_cfg: Dict[str, Any] = self.config.get("telegram", {})
        hyperliquid_cfg: Dict[str, Any] = self.config.get("hyperliquid", {})

        bot_token: Optional[str] = telegram_cfg.get("bot_token")
        if not bot_token or not re.match(r"^\d+:[\w-]{35,}$", bot_token):
            errors.append("Invalid telegram.bot_token format.")

        user_id: Optional[int] = telegram_cfg.get("user_id")
        if not isinstance(user_id, int):
            errors.append("telegram.user_id must be an integer.")

        api_key: Optional[str] = hyperliquid_cfg.get("wallet_address")
        api_secret: Optional[str] = hyperliquid_cfg.get("private_key")

        if not api_key:
            errors.append("Missing hyperliquid.wallet_address.")
        if not api_secret:
            errors.append("Missing hyperliquid.private_key.")

        if errors:
            raise ConfigError("Config validation errors:\n" + "\n".join(errors))

    def _load_exchange(self) -> None:
        """
        Loads the Hyperliquid exchange instance using the config values.

        It creates an Ethereum account using the private key, and then
        creates an instance of the Hyperliquid Exchange class using the
        account, base URL (testnet or mainnet), and the wallet address.

        It logs the chosen base URL to the logger.

        If the private key is invalid, it raises a ConfigError.
        """
        private_key: str = self.config["hyperliquid"]["private_key"]
        address: str = self.config["hyperliquid"]["wallet_address"]
        testnet: bool = self.config["hyperliquid"]["testnet"]
        skip_ws = True
        
        if testnet:
            base_url: str = constants.TESTNET_API_URL
            logger.info(f"hl: Using testnet - {base_url}")
        else:
            base_url: str = constants.MAINNET_API_URL
            logger.info(f"hl: Using mainnet - {base_url}")
        
        # load ethereum account from private key
        try:
            account = Account.from_key(private_key)
        except (ValidationError, ValueError):
            raise ConfigError("Invalid private key provided.")
            
        if not is_checksum_address(account.address):
            raise ConfigError("Invalid private key provided.")
        
        self.exchange: Exchange = Exchange(wallet=account, base_url=base_url, 
                                           account_address=address)
        
    async def _validate_hyperliquid(self, config: dict) -> None:
        try:
            address: str = self.config["hyperliquid"]["wallet_address"]
            self._load_exchange()
            info: Info = self.exchange.info
            try:
                user_state = info.user_state(address)
                # Get the user state and print out position information
                spot_user_state = info.spot_user_state(address)
            except error.ClientError as e:
                raise ConfigError(f"Error getting user state: {e}")
            if len(spot_user_state["balances"]) > 0:
                logger.info("spot balances:")
                for balance in spot_user_state["balances"]:
                    print(json.dumps(balance, indent=2))
            else:
                raise ConfigError("No available balances; Please deposit some USDC on the exchange to start.")
            margin_summary = user_state["marginSummary"]
            print(user_state)
            if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
                print("Exiting because the provided account has no equity.")
                url = info.base_url.split(".", 1)[1]
                error_string = f"No accountValue:\nIf you think this is a mistake, make sure that {address} has a balance on {url}."
                raise ConfigError(error_string)
            # Place a test order with the agent (setting a very low price so that it rests in the order book).
            # The order is placed as a "limit" order with the time-in-force set to "Good till Cancelled" (GTC).
            # This allows us to test placing an order without immediately executing it.
            SPOT_ETH_PAIR = "UETH/USDC"
            eth_price = int(HyperliquidManager(self.exchange).get_spot_price(SPOT_ETH_PAIR))
            # to do a test order, we buy eth at 50% of the current price
            test_buy_price = int(eth_price * 0.5)
            print(f"test keys -- placing an Ioc order of {0.05} ETH at {test_buy_price}")
            order_result = self.exchange.order(SPOT_ETH_PAIR, True, 0.05, test_buy_price, {"limit": {"tif": "Ioc"}})
            print(order_result)

            # If the order was placed successfully and the status is "resting," we attempt to cancel it.
            # This simulates the process of managing orders and ensuring that orders are no longer needed are cleaned up.
            # However, with Ioc order, we don't have to call the cancel order. it will get auto cancelled.
            # {'status': 'ok', 'response': {'type': 'order', 'data': {'statuses': [{'error': 'Order could not immediately match against any resting orders. asset=11137'}]}}}
            if order_result["status"] == "ok":
                status = order_result["response"]["data"]["statuses"][0]
                if "resting" in status:
                    cancel_result = self.exchange.cancel(SPOT_ETH_PAIR, status["resting"]["oid"])
                    print(cancel_result)
                else:
                    # this failure is expected as we try to execute buy order at half price
                    if status["error"].startswith("Order could not immediately match against any resting orders."):
                        print("test keys -- OK")
                    else:
                        raise ConfigError(f"Test order failed: {order_result}")
            else:
                raise ConfigError(f"Test order failed: {order_result}")
            
            if self.config_hash != "":
                db_path = self.get_db_path()
                await InternalConfig(db_path).set("config_hash", self.config_hash)
            else:
                logger.warning("No config hash found in config.")
                
            logger.info("Hyperliquid validation successful.")
        except Exception as e:
            logging.exception(e)
            raise ConfigError(f"Hyperliquid SDK validation failed: {e}")

    async def _external_validation(self) -> None:
        telegram_cfg: Dict[str, Any] = self.config["telegram"]
        bot_token: str = telegram_cfg["bot_token"]
        user_id: int = telegram_cfg["user_id"]

        try:
            bot: Bot = Bot(token=bot_token)
            user: Chat = await bot.get_chat(user_id)
            print(f"Telegram user validation successful: {user.first_name} ({user.id})")
        except TelegramError as e:
            raise ConfigError(f"Telegram API validation failed: {e}")

        hyperliquid_cfg = self.config["hyperliquid"]
        await self._validate_hyperliquid(
            config=hyperliquid_cfg
        )

    async def validate(self) -> None:
        """
        Validate the configuration by performing a series of checks.

        This function performs the following steps:
            * Loads the configuration from the YAML file.
            * Performs initial validation checks on the config values.
            * Conducts external validation to ensure integration with external systems.

        Raises:
            ConfigError: If any validation step fails.
        """

        config_changed: bool = await self.load_config()
        # Perform validation if the config has changed since the last successful run
        if config_changed:
            self.initial_validation()
            await self._external_validation()
        else:
            # load exchange
            self._load_exchange()

    def get_config(self) -> Dict[str, Any]:
        return self.config
