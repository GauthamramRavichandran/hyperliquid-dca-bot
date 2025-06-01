from datetime import datetime
import json
import logging
from typing import Optional, List, Dict

from ..backend.exceptions import DuplicateLabelError
from ..backend.main import BaseDB

logger = logging.getLogger(__name__)


class SIPConfig(BaseDB):
    def __init__(self, db_path: str):
        super().__init__(db_path)
        
    async def add_config(
        self,
        label: str,
        coins: Dict[str, int],
        interval: str,
        amount: str,
        enabled: bool = True
    ) -> None:
        existing = await self.fetch_one(
        "SELECT 1 FROM sip_config WHERE label = ?", (label,)
    )
        if existing:
            raise DuplicateLabelError(label)
        now = datetime.utcnow().isoformat()
        coins_json = json.dumps(coins)
        await self.execute(
            """
            INSERT INTO sip_config
            (label, coins, interval, amount, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                label,
                coins_json,
                interval,
                amount,
                enabled,
                now
            )
        )
        logger.info(f"Inserted/updated SIP config for label: '{label}'")

    async def get_config(self, id: str) -> Optional[Dict]:
        row = await self.fetch_one("SELECT * FROM sip_config WHERE id = ?", (id,))
        if row:
            logger.info(f"Fetched SIP config for id: '{id}'")
            return dict(row)
        return None

    async def get_config_by_label(self, label: str) -> Optional[Dict]:
        row = await self.fetch_one("SELECT * FROM sip_config WHERE label = ?", (label,))
        if row:
            logger.info(f"Fetched SIP config for label: '{label}'")
            return dict(row)
        return None

    async def get_all_configs(self) -> List[Dict]:
        rows = await self.fetch_all("SELECT * FROM sip_config")
        logger.info("Fetched all SIP configs")
        return [dict(row) for row in rows]

    async def get_active_configs(self) -> List[Dict]:
        rows = await self.fetch_all("SELECT * FROM sip_config WHERE enabled = 1")
        logger.info("Fetched active SIP configs")
        return [dict(row) for row in rows]

    async def delete_config(self, id: str) -> None:
        await self.execute("DELETE FROM sip_config WHERE id = ?", (id,))
        logger.info(f"Deleted SIP config for id: '{id}'")
