# 🧠 Hyperliquid DCA Bot

A self-hosted Telegram bot to automate Dollar-Cost Averaging (DCA) strategies (similar to SIPs) on the [Hyperliquid](https://hyperliquid.xyz) exchange.

### ✨ Features

- 🧩 Multiple DCA strategies (e.g. BTC every 12h, ETH/SOL weekly)

- 🔧 Fully managed through Telegram — no manual editing needed
- ⏱️ Flexible intervals: hourly, daily, weekly — you choose
- 🚧 Testnet Support: Run SIP strategies safely on the testnet to validate your setups without risking real funds.
- 🔐 Simplified Authentication: Only the private key of your API wallet address is needed for SIP operations — no need to share your entire wallet.
- 🗃️ Config stored in SQLite (strategies + execution history)
- 🏗️ Easy to run — minimal setup, zero dependencies outside Python

> **Attention:** This bot is exclusively intended for personal use. Security measures are your sole responsibility when deploying it.


### Installation

1. **Install Python dependencies**:
	* Install `uv` via [standalone installer](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) or your package manager.
	* Create a new virtual environment with `uv env` (it will reside in `.venv` folder by default).
2. **Activate the virtual environment**:
	* `source .venv/bin/activate` (on Unix-like systems) or
	* `.venv\Scripts\activate` (on Windows)


### Project Structure
```
├── README.md
├── bot/
│   ├── backend/         # DB Logic: SIP management/execution history
│   ├── callbacks/       # Callback handlers
│   ├── common/          # Shared helper functions
│   ├── const/           # Constants, keyboards, config
│   ├── handlers/        # Command/message handlers for bot
│   ├── translations/    # i18n support
│   └── models/          # Custom classes for bot functionality
├── run.py               # Entrypoint to start bot
├── requirements.txt     # Dependencies
```