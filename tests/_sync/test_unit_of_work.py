import pytest

from messagebus.domain.model import GenericEvent
from messagebus.service._sync.unit_of_work import (
    SyncUnitOfWorkTransaction,
    TransactionError,
    TransactionStatus,
)
from tests._sync.conftest import (
    DummyMetricsStore,
    DummyModel,
    MyMetadata,
    SyncDummyUnitOfWork,
)


class FooCreated(GenericEvent[MyMetadata]):
    id: str
    metadata: MyMetadata = MyMetadata(
        name="foo_created",
        schema_version=1,
        published=True,
        custom_field="",
    )


class BarCreated(GenericEvent[MyMetadata]):
    metadata: MyMetadata = MyMetadata(
        name="bar_created",
        schema_version=1,
        published=True,
        custom_field="",
    )


def test_collect_new_events(uow: SyncDummyUnitOfWork, foo_factory: type[DummyModel]):
    foo = foo_factory(id="1", counter=0)
    foo.messages.append(FooCreated(id="1"))
    bar = foo_factory(id="1", counter=0)
    bar.messages.append(BarCreated())
    foo2 = foo_factory(id="2", counter=0)
    foo2.messages.append(FooCreated(id="2"))

    with uow as tuow:
        tuow.foos.add(foo)
        tuow.bars.add(bar)
        tuow.foos.add(foo2)
        tuow.commit()

    iter = uow.collect_new_events()
    assert next(iter) == FooCreated(id="1")
    assert next(iter) == FooCreated(id="2")
    assert next(iter) == BarCreated()
    with pytest.raises(StopIteration):
        next(iter)


def test_transaction_rollback_on_error(
    uow: SyncDummyUnitOfWork, metrics: DummyMetricsStore
):
    tuow = None
    try:
        with uow as tuow:
            raise ValueError("Boom")
    except Exception:
        ...
    assert tuow is not None
    assert tuow.status == TransactionStatus.rolledback
    assert metrics.dump() == {
        "beginned_transaction_count": 1,
        "transaction_commit_count": 0,
        "transaction_failed_count": 1,
        "transaction_rollback_count": 1,
        "processed_count": {},
    }


def test_transaction_rollback_explicit_commit(
    uow: SyncDummyUnitOfWork, metrics: DummyMetricsStore
):
    with pytest.raises(TransactionError) as ctx:
        with uow as tuow:
            tuow.foos  # noqa B018

    assert str(ctx.value).endswith(
        "Transaction must be explicitly close. Missing commit/rollback call."
    )
    assert metrics.dump() == {
        "beginned_transaction_count": 1,
        "transaction_commit_count": 0,
        "transaction_failed_count": 0,
        "transaction_rollback_count": 0,
        "processed_count": {},
    }


def test_transaction_invalid_state(
    uow: SyncDummyUnitOfWork, metrics: DummyMetricsStore
):
    with pytest.raises(TransactionError) as ctx:
        with uow as tuow:
            tuow.status = TransactionStatus.closed

    assert str(ctx.value).endswith("Transaction is closed.")
    assert metrics.dump() == {
        "beginned_transaction_count": 1,
        "transaction_commit_count": 0,
        "transaction_failed_count": 0,
        "transaction_rollback_count": 0,
        "processed_count": {},
    }


def test_transaction_invalid_usage(
    uow: SyncDummyUnitOfWork, metrics: DummyMetricsStore
):
    with pytest.raises(TransactionError) as ctx:
        transaction = SyncUnitOfWorkTransaction(uow)
        transaction.status = TransactionStatus.committed
        with transaction:
            ...

    assert str(ctx.value).endswith("Invalid transaction status.")
    assert metrics.dump() == {
        "beginned_transaction_count": 0,
        "transaction_commit_count": 0,
        "transaction_failed_count": 0,
        "transaction_rollback_count": 0,
        "processed_count": {},
    }


def test_transaction_commit_after_rollback(
    uow: SyncDummyUnitOfWork, metrics: DummyMetricsStore
):
    with pytest.raises(TransactionError) as ctx:
        with uow as tuow:
            tuow.rollback()
            tuow.commit()

    assert str(ctx.value).endswith("Transaction already closed (rolledback).")
    assert metrics.dump() == {
        "beginned_transaction_count": 1,
        "transaction_commit_count": 0,
        "transaction_failed_count": 1,
        "transaction_rollback_count": 1,
        "processed_count": {},
    }


def test_transaction_commit_twice(uow: SyncDummyUnitOfWork, metrics: DummyMetricsStore):
    with pytest.raises(TransactionError) as ctx:
        with uow as tuow:
            tuow.commit()
            tuow.commit()

    assert str(ctx.value).endswith("Transaction already closed (committed).")
    assert metrics.dump() == {
        "beginned_transaction_count": 1,
        "transaction_commit_count": 0,
        "transaction_failed_count": 1,
        "transaction_rollback_count": 1,
        "processed_count": {},
    }


def test_detach_transaction(uow: SyncDummyUnitOfWork, metrics: DummyMetricsStore):
    with uow as tuow:
        uow.foos.add(DummyModel(id="1", counter=1))
        uow.foos.add(DummyModel(id="2", counter=1))
        uow.foos.add(DummyModel(id="3", counter=1))
        tuow.commit()

    assert metrics.dump() == {
        "beginned_transaction_count": 1,
        "transaction_commit_count": 1,
        "transaction_failed_count": 0,
        "transaction_rollback_count": 0,
        "processed_count": {},
    }

    with uow as tuow:
        iter_foos = uow.foos.find(id="2")
        tuow.detach()

    assert metrics.dump() == {
        "beginned_transaction_count": 2,
        "transaction_commit_count": 1,
        "transaction_failed_count": 0,
        "transaction_rollback_count": 0,
        "processed_count": {},
    }

    try:
        foos = [foo for foo in iter_foos]
        assert foos == [DummyModel(id="2", counter=1)]
    finally:
        tuow.close()

    assert metrics.dump() == {
        "beginned_transaction_count": 2,
        "transaction_commit_count": 1,
        "transaction_failed_count": 0,
        "transaction_rollback_count": 1,
        "processed_count": {},
    }
