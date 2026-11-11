from datetime import UTC
from typing import Any

from sqlalchemy import Dialect
from sqlalchemy.types import DateTime, TypeDecorator


class TZAwareDateTime(TypeDecorator[DateTime]):
    """
    Set a timezone to UTC if the timezone has not been set in the database.
    Used for testing with sqlite.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("naive datetime is disallowed")
        return value

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value
