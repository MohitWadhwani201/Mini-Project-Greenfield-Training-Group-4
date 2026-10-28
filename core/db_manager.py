"""Thread-safe Singleton DatabaseConnection with per-database connection pools."""
import threading
from contextlib import contextmanager
from typing import Any, Iterator, Optional, Sequence

import mysql.connector
from mysql.connector import errorcode, pooling

from config import DBSettings, load_settings
from exceptions import DatabaseOperationError, DuplicateEntityError


class DatabaseConnection:
    """Singleton managing MySQL pools for the OLTP and OLAP databases.

    Usage:
        db = DatabaseConnection()
        rows = db.fetch_all("SELECT * FROM employees WHERE department_id=%s", (3,))
        with db.transaction() as cur:
            cur.execute(...); cur.execute(...)   # commit on success, rollback on error
    """

    _instance: Optional["DatabaseConnection"] = None
    _instance_lock = threading.Lock()

    def __new__(cls, settings: Optional[DBSettings] = None):
        if cls._instance is None:                      # fast path
            with cls._instance_lock:
                if cls._instance is None:              # double-checked locking
                    inst = super().__new__(cls)
                    inst._settings = settings or load_settings()
                    inst._pools = {}
                    inst._pool_lock = threading.Lock()
                    cls._instance = inst
        return cls._instance

    # ---- configuration -------------------------------------------------
    @property
    def settings(self) -> DBSettings:
        return self._settings

    @property
    def oltp_name(self) -> str:
        return self._settings.oltp_db

    @property
    def olap_name(self) -> str:
        return self._settings.olap_db

    @classmethod
    def reset_instance(cls) -> None:
        """Drop the singleton (used by tests)."""
        with cls._instance_lock:
            cls._instance = None

    # ---- pooling -------------------------------------------------------
    def _get_pool(self, database: str) -> pooling.MySQLConnectionPool:
        pool = self._pools.get(database)
        if pool is None:
            with self._pool_lock:
                pool = self._pools.get(database)
                if pool is None:
                    s = self._settings
                    try:
                        pool = pooling.MySQLConnectionPool(
                            pool_name=f"pool_{database}"[:32], pool_size=s.pool_size,
                            host=s.host, port=s.port, user=s.user,
                            password=s.password, database=database,
                        )
                    except mysql.connector.Error as exc:
                        raise DatabaseOperationError(
                            f"Cannot create pool for '{database}': {exc}") from exc
                    self._pools[database] = pool
        return pool

    def get_connection(self, database: Optional[str] = None):
        db = database or self.oltp_name
        try:
            return self._get_pool(db).get_connection()
        except mysql.connector.Error as exc:
            raise DatabaseOperationError(f"Cannot get connection: {exc}") from exc

    @staticmethod
    def _translate(exc: mysql.connector.Error) -> Exception:
        if getattr(exc, "errno", None) == errorcode.ER_DUP_ENTRY:
            return DuplicateEntityError(str(exc))
        return DatabaseOperationError(str(exc))

    # ---- transactions & queries ---------------------------------------
    @contextmanager
    def transaction(self, database: Optional[str] = None) -> Iterator[Any]:
        """Yield a dict cursor; commit on success, rollback on any exception."""
        conn = self.get_connection(database)
        cur = conn.cursor(dictionary=True)
        try:
            yield cur
            conn.commit()
        except mysql.connector.Error as exc:
            conn.rollback()
            raise self._translate(exc) from exc
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()   # returns connection to the pool

    def fetch_all(self, query: str, params: Optional[Sequence] = None,
                  database: Optional[str] = None) -> list[dict]:
        conn = self.get_connection(database)
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params or ())
            rows = cur.fetchall()
            cur.close()
            return rows
        except mysql.connector.Error as exc:
            raise self._translate(exc) from exc
        finally:
            conn.close()

    def fetch_one(self, query: str, params: Optional[Sequence] = None,
                  database: Optional[str] = None) -> Optional[dict]:
        rows = self.fetch_all(query, params, database)
        return rows[0] if rows else None

    def execute_query(self, query: str, params: Optional[Sequence] = None,
                      database: Optional[str] = None) -> int:
        """Run a write statement in its own transaction; returns lastrowid."""
        with self.transaction(database) as cur:
            cur.execute(query, params or ())
            return cur.lastrowid

    def execute_many(self, query: str, seq_params: Sequence[Sequence],
                     database: Optional[str] = None) -> int:
        with self.transaction(database) as cur:
            cur.executemany(query, seq_params)
            return cur.rowcount
