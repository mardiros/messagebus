import abc
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

from messagebus.domain.model import GenericCommand, Metadata, TransactionStatus


class AbstractMetricsStore(abc.ABC):
    @abc.abstractmethod
    def inc_beginned_transaction_count(self) -> None: ...

    @abc.abstractmethod
    def inc_transaction_failed(self) -> None: ...

    @abc.abstractmethod
    def inc_transaction_closed_count(self, status: TransactionStatus) -> None: ...

    @abc.abstractmethod
    def inc_messages_processed_total(self, msg_metadata: Metadata) -> None: ...

    @abc.abstractmethod
    @contextmanager
    def command_processing_timer(
        self, command: GenericCommand[Any]
    ) -> Iterator[None]: ...


class SinkholeMetricsStore(AbstractMetricsStore):
    def inc_beginned_transaction_count(self) -> None: ...

    def inc_transaction_failed(self) -> None: ...

    def inc_transaction_closed_count(self, status: TransactionStatus) -> None: ...

    def inc_messages_processed_total(self, msg_metadata: Metadata) -> None: ...

    @contextmanager
    def command_processing_timer(self, command: GenericCommand[Any]) -> Iterator[None]:
        yield  # coverage: ignore


TMetricsStore = TypeVar("TMetricsStore", bound=AbstractMetricsStore)
