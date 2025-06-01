from dataclasses import dataclass
from typing import Literal

@dataclass
class Pair:
    symbol: str                # e.g. "ETH/USDC"
    price: float               # Current price
    market_type: Literal["spot", "perp"]  # Market type
    base_token: str            # e.g. "ETH"
    quote_token: str           # e.g. "USDC"
    sz_decimals: int           # e.g. 6

    def __repr__(self):
        return f"Pair(symbol={self.symbol}, price={self.price}, market_type={self.market_type}, base_token={self.base_token}, quote_token={self.quote_token})"
    
    def __str__(self):
        return f"<b>{self.symbol}</b>\nPrice: {self.price:.2f}\nMarket: {self.market_type}\nBase: {self.base_token}\nQuote: {self.quote_token}"
