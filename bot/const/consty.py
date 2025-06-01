class STATES:
    LABEL, COINS, INTERVAL, AMOUNT, CONFIRMATION = range(5)

# Mapping of coin to spot pair in Hyperliquid
SpotPairMapping: dict[str, str] = {"BTC": "BTC/USDC",
                         "ETH": "UETH/USDC",
                         "SOL": "USOL/USDC",}
# Available testnet pairs
TestnetPairs: dict[str, str] = {"HYPE": "HYPE/USDC",
                                "ETH": "UETH/USDC",
                                "PURR": "PURR/USDC",}
    