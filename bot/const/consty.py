class STATES:
    LABEL, COINS, INTERVAL, AMOUNT, CONFIRMATION = range(5)


# Mapping of coin to spot pair in Hyperliquid
coin_mapping: dict[str, str] = {"BTC": "UBTC",
                                "ETH": "UETH",
                                "SOL": "USOL",}
# Available testnet pairs
testnet_pairs: dict[str, str] = {"HYPE": "HYPE/USDC",
                                "ETH": "UETH/USDC",
                                "PURR": "PURR/USDC",}
    