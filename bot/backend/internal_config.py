from datetime import datetime
import logging
from pathlib import Path
from typing import Optional

import aiosqlite

from .main import BaseDB

# Setup logger
logger = logging.getLogger(__name__)

class InternalConfig(BaseDB):
    def __init__(self, db_path: str):
        super().__init__(db_path)
    async def get(self, key: str) -> Optional[str]:
        """
        Fetches a value from the internal_config table by key.

        Args:
            key: The key to look up in the internal_config table.

        Returns:
            The value associated with the given key, or None if the key does not exist.
        """
        row = await self.fetch_one("SELECT value FROM internal_config WHERE id = ?", (key,))
        if row:
            logger.info(f"Fetched config value for key: '{key}'")
            return row['value']
        logger.warning(f"No config value found for key: '{key}'")
        return None

    async def set(self, key: str, value: str) -> None:
        now: str = datetime.utcnow().isoformat()
        await self.execute(
            """
            INSERT INTO internal_config (id, value, last_updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                value = excluded.value,
                last_updated_at = excluded.last_updated_at
            """,
            (key, value, now),
        )
        logger.info(f"Set config value for key: '{key}' - '{value}'")

    async def delete(self, key: str) -> None:
        await self.execute("DELETE FROM internal_config WHERE id = ?", (key,))
        logger.info(f"Deleted config key: '{key}'")