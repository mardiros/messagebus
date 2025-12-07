import abc
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any, ClassVar

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge
from prometheus_client.metrics import Histogram

from messagebus.domain.model import GenericCommand, Metadata, TransactionStatus
from messagebus.ports.observability import AbstractMetricsStore

DEFAULT_COMMAND_PROCESSING_SECONDS_BUCKETS = [0.01 * 2**x for x in range(10)]


class Singleton(abc.ABCMeta):
    """
    Ensure the REGISTRY will not raises a duplicate timeseries by reusing it.

    Since we as an Async and a Sync version we got two instances of the MetricStore,
    and to avoid gen unasync code, this singleton ensure we have one class.
    The registry in parameter ensure the class behave properly by registry,
    and might create memory leaks if misused.
    """

    _instances: ClassVar[dict[tuple[type, int], Any]] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        registry = kwargs.get("registry") or REGISTRY

        key = (cls, id(registry))
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]


class MetricsStore(AbstractMetricsStore, metaclass=Singleton):
    def __init__(
        self,
        *,
        registry: CollectorRegistry = REGISTRY,
        command_processing_seconds_buckets: Sequence[
            float | str
        ] = DEFAULT_COMMAND_PROCESSING_SECONDS_BUCKETS,
    ) -> None:
        self.transactions_started_total = Counter(
            name="messagebus_transactions_started_total",
            documentation="Total number of unit-of-work transactions that have been started.",
            registry=registry,
        )

        self.transactions_in_progress = Gauge(
            name="messagebus_transactions_in_progress",
            documentation="Current number of unit-of-work transactions in progress.",
            registry=registry,
        )

        self.transactions_failed_total = Counter(
            name="messagebus_transactions_failed_total",
            documentation="Total number of unit-of-work transactions rolled back due to an exception.",
            registry=registry,
        )

        self.transactions_closed_total = Counter(
            name="messagebus_transactions_closed_total",
            documentation="Total number of unit-of-work transactions that have been committed or rolled back.",
            labelnames=["status"],
            registry=registry,
        )

        self.messages_processed_total = Counter(
            name="messagebus_messages_processed_total",
            documentation="Total number of messages that has been handled handled by the bus.",
            labelnames=["name", "version"],
            registry=registry,
        )

        self.command_processing_seconds = Histogram(
            name="messagebus_command_processing_seconds",
            documentation="Time spent processing a command in the bus",
            labelnames=["name", "version"],
            registry=registry,
            buckets=command_processing_seconds_buckets,
        )

    def inc_beginned_transaction_count(self) -> None:
        self.transactions_started_total.inc()
        self.transactions_in_progress.inc()

    def inc_transaction_failed(self) -> None:
        self.transactions_failed_total.inc()

    def inc_transaction_closed_count(self, status: TransactionStatus) -> None:
        self.transactions_closed_total.labels(status=status.name).inc()
        self.transactions_in_progress.dec()

    def inc_messages_processed_total(self, msg_metadata: Metadata) -> None:
        self.messages_processed_total.labels(
            name=msg_metadata.name, version=msg_metadata.schema_version
        ).inc()

    @contextmanager
    def command_processing_timer(self, command: GenericCommand[Any]) -> Iterator[None]:
        with self.command_processing_seconds.labels(
            name=command.metadata.name, version=command.metadata.schema_version
        ).time():
            yield
