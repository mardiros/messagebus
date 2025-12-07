from collections.abc import Iterator

import pytest
from prometheus_client import CollectorRegistry

from messagebus import Metadata, TransactionStatus
from messagebus.infrastructure.observability.metrics import MetricsStore, Singleton


@pytest.fixture()
def registry() -> CollectorRegistry:
    return CollectorRegistry()


@pytest.fixture()
def metrics(registry: CollectorRegistry) -> Iterator[MetricsStore]:
    yield MetricsStore(registry=registry)
    del Singleton._instances[(MetricsStore, id(registry))]


def test_prometheus_transaction_commit(
    metrics: MetricsStore, registry: CollectorRegistry
):
    metrics.inc_beginned_transaction_count()
    assert registry.get_sample_value("messagebus_transactions_started_total") == 1
    assert registry.get_sample_value("messagebus_transactions_in_progress") == 1
    assert registry.get_sample_value("messagebus_transactions_failed_total") == 0
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "committed"}
        )
        is None
    )
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "rolledback"}
        )
        is None
    )

    metrics.inc_transaction_closed_count(TransactionStatus.committed)
    assert registry.get_sample_value("messagebus_transactions_started_total") == 1
    assert registry.get_sample_value("messagebus_transactions_in_progress") == 0
    assert registry.get_sample_value("messagebus_transactions_failed_total") == 0
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "committed"}
        )
        == 1
    )
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "rolledback"}
        )
        is None
    )


def test_prometheus_transaction_rollback(
    metrics: MetricsStore, registry: CollectorRegistry
):
    metrics.inc_beginned_transaction_count()
    assert registry.get_sample_value("messagebus_transactions_started_total") == 1
    assert registry.get_sample_value("messagebus_transactions_in_progress") == 1
    assert registry.get_sample_value("messagebus_transactions_failed_total") == 0
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "committed"}
        )
        is None
    )
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "rolledback"}
        )
        is None
    )

    metrics.inc_transaction_closed_count(TransactionStatus.rolledback)
    assert registry.get_sample_value("messagebus_transactions_started_total") == 1
    assert registry.get_sample_value("messagebus_transactions_in_progress") == 0
    assert registry.get_sample_value("messagebus_transactions_failed_total") == 0
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "committed"}
        )
        is None
    )
    assert (
        registry.get_sample_value(
            "messagebus_transactions_closed_total", labels={"status": "rolledback"}
        )
        == 1
    )


def test_prometheusinc_inc_messages_processed_total(
    metrics: MetricsStore, registry: CollectorRegistry
):
    metrics.inc_messages_processed_total(Metadata(name="dummy", schema_version=42))
    assert (
        registry.get_sample_value(
            "messagebus_messages_processed_total",
            labels={"name": "dummy", "version": "42"},
        )
        == 1
    )
