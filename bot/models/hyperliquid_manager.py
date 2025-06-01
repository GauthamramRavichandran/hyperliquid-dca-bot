from typing import Optional
from hyperliquid.exchange import Exchange


class HyperliquidManager:
    def __init__(self, exchange: Exchange):
        self.exchange = exchange
    
    def get_spot_price(self, token_name: str) -> Optional[float]:
        """
        Fetches the current spot price (markPx) for a given token name (e.g., "UETH" or "UETH/USDC") on Hyperliquid.

        :param token_name: Name of the token, like "UETH"
        :return: Spot price as float
        """
        if token_name is None:
            return None
        meta, asset_ctxs = self.exchange.info.spot_meta_and_asset_ctxs()
        if "/"  in token_name:
            token_name: str = token_name.split("/")[0]
            
        # Step 1: Get token index from token_name
        token_index = None
        for token in meta["tokens"]:
            if token["name"] == token_name:
                token_index = token["index"]
                break
        if token_index is None:
            raise ValueError(f"Token '{token_name}' not found.")

        # Step 2: Find coin name in universe using token_index
        coin_name = None
        for asset in meta["universe"]:
            # 0th index is the USDC token; an extra check, to make sure quote token is in USDC
            if asset["tokens"][0] == token_index and asset["tokens"][1] == 0:
                coin_name: str = asset["name"]
                break
        if coin_name is None:
            raise ValueError(f"Coin name for token '{token_name}' not found.")

        # Step 3: Find markPx from asset_ctxs by coin name
        for ctx in asset_ctxs:
            if ctx["coin"] == coin_name:
                return float(ctx["markPx"])

        raise ValueError(f"Price for coin '{coin_name}' not found.")

