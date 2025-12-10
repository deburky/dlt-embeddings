"""Type stubs for dlt.destinations.sql_client module."""

from typing import Any, Protocol, ClassVar

class SqlClientBase(Protocol):
    """Base SQL client interface."""

    def execute_sql(self, sql: str, *args: Any, **kwargs: Any) -> Any: ...
    def execute_query(self, query: str, *args: Any, **kwargs: Any) -> Any: ...

    # Class methods that can be patched
    create_dataset: ClassVar[Any] = ...
