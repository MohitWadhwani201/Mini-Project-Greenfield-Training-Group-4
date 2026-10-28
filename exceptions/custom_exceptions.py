"""Custom exception hierarchy. The UI can catch AppError to show friendly messages."""


class AppError(Exception):
    """Base class for all application errors."""


class DatabaseOperationError(AppError):
    """A database call failed (connection, query, transaction)."""


class EntityNotFoundError(AppError):
    """Requested entity does not exist."""

    def __init__(self, entity: str, entity_id):
        super().__init__(f"{entity} with id={entity_id} not found")
        self.entity, self.entity_id = entity, entity_id


class ValidationError(AppError):
    """Entity attribute failed validation."""


class DuplicateEntityError(AppError):
    """Unique constraint violated (e.g. duplicate email)."""

class WarehouseSyncError(DatabaseOperationError):
    """OLTP change was saved, but the OLAP/ETL step failed.

    The ETL procedures are idempotent, so the next ETL run will reconcile it.
    """
