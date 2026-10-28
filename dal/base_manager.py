"""BaseManager: shared DB plumbing for every manager (inheritance per spec)."""
from typing import Optional, Sequence

from core.db_manager import DatabaseConnection


class BaseManager:
    def __init__(self, db: Optional[DatabaseConnection] = None):
        self._db = db or DatabaseConnection()

    @property
    def oltp(self) -> str:
        return self._db.oltp_name

    @property
    def olap(self) -> str:
        return self._db.olap_name

    def _fetch_all(self, sql: str, params: Optional[Sequence] = None, olap: bool = False):
        return self._db.fetch_all(sql, params, self.olap if olap else self.oltp)

    def _fetch_one(self, sql: str, params: Optional[Sequence] = None, olap: bool = False):
        return self._db.fetch_one(sql, params, self.olap if olap else self.oltp)
