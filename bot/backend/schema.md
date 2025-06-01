# SIP Database Schema

## Table: `sip_config`

### Columns:

- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  Unique identifier for each SIP strategy.

- `label`: TEXT NOT NULL
  A user-friendly name for the SIP strategy.

- `coins`: TEXT NOT NULL
  JSON string representing coin allocations.
  Example: '{"btc": 60, "eth": 40}' means 60% BTC, 40% ETH.

- `interval`: TEXT NOT NULL
  The frequency of investments, e.g., '12h', '1d', '1w'.

- `amount`: REAL NOT NULL
  The total USD amount to invest per interval.

- `enabled`: INTEGER NOT NULL DEFAULT 1
  Flag to indicate if the strategy is active (1) or paused (0).

- `created_at`: TEXT NOT NULL
  Timestamp when the strategy was created, in ISO format.

## Table: `sip_history`

### Columns:

- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  Unique identifier for each SIP execution record.

- `config_id`: INTEGER NOT NULL
  Foreign key linking to the `sip_config` strategy that triggered this record.

- `executed_at`: TEXT NOT NULL
  Timestamp when the SIP execution happened, in ISO 8601 format.

- `coin`: TEXT NOT NULL
  The symbol of the coin that was purchased (e.g., 'btc', 'eth').

- `amount_usd`: REAL NOT NULL
  The USD amount spent to buy the coin.

- `size_received`: REAL NOT NULL
  The quantity of the coin received after purchase.

- `coin_price_usd`: REAL NOT NULL
  The price of the coin in USD at the time of purchase.

- `fee_usd`: REAL NOT NULL
  The fee paid in USD for this purchase.

## Table: `internal_config`

### Columns:
- `id`: TEXT NOT NULL
  Unique identifier for each record

- `value`: TEXT NOT NULL
  Value of the record, preferrably a json string

- `last_updated_at`: TEXT NOT NULL
  Timestamp when the record updated at, in ISO 8601 format.

