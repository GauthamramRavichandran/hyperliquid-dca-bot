import logging
from pathlib import Path
from typing import List

import aiosqlite

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BaseDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def execute(self, query: str, params: tuple = ()) -> None:
        """
        Execute a SQL query on the database.

        :param query: The SQL query to execute. This query should not contain any user-provided data.
        :param params: A tuple of parameters to substitute into the query. This should include any user-provided data.
        :raises: Any exceptions that occur during database access will be logged and then re-raised.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, params)
                await db.commit()
        except Exception as e:
            logger.error(f"DB execute error: {e}")
            raise e

    async def fetch_one(self, query: str, params: tuple = ()) -> dict:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return {col[0]: row[i] for i, col in enumerate(cursor.description)}
                    return {}
        except Exception as e:
            logger.error(f"DB fetch_one error: {e}")
            raise e
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[aiosqlite.Row]:
        """
        Execute a SQL query and return all matching rows as a list of aiosqlite.Row objects.

        :param query: The SQL query to execute. This query should not contain any user-provided data.
        :param params: A tuple of parameters to substitute into the query. This should include any user-provided data.
        :return: A list of rows from the database. Each row is an aiosqlite.Row object.
        :raises: Any exceptions that occur during database access will be logged and then re-raised.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return rows
