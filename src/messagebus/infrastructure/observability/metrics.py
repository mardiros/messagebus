import abc

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge

from messagebus.domain.model import TransactionStatus


class AbstractMetricsStore(abc.ABC):
    @abc.abstractmethod
    def inc_beginned_transaction_count(self) -> None: ...

    @abc.abstractmethod
    def inc_transaction_failed(self) -> None: ...

    @abc.abstractmethod
    def inc_transaction_closed_count(self, status: TransactionStatus) -> None: ...


class MetricsStore(AbstractMetricsStore):
    _instance = None
    _initialized = False

    def __new__(cls, registry: CollectorRegistry | None = REGISTRY) -> "MetricsStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, registry: CollectorRegistry | None = REGISTRY) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.transactions_started_total = Counter(
            name="messagebus_transactions_started_total",
            documentation="Total number of unit-of-work transactions that have been started.",
        )

        self.transactions_in_progress = Gauge(
            name="messagebus_transactions_in_progress",
            documentation="Current number of unit-of-work transactions in progress.",
        )

        self.transactions_failed_total = Counter(
            name="messagebus_transactions_failed_total",
            documentation="Total number of unit-of-work transactions rolled back due to an exception.",
        )

        self.transactions_closed_total = Counter(
            name="messagebus_transactions_closed_total",
            documentation="Total number of unit-of-work transactions that have been committed or rolled back.",
            labelnames=["status"],
        )

    def inc_beginned_transaction_count(self) -> None:
        self.transactions_started_total.inc()
        self.transactions_in_progress.inc()

    def inc_transaction_failed(self) -> None:
        self.transactions_failed_total.inc()

    def inc_transaction_closed_count(self, status: TransactionStatus) -> None:
        self.transactions_closed_total.labels(status=status.name).inc()
        self.transactions_in_progress.dec()
