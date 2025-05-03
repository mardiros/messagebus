import pytest

from messagebus.domain.model import GenericEvent
from messagebus.service._async.unit_of_work import (
    AsyncUnitOfWorkTransaction,
    TransactionError,
    TransactionStatus,
)
from tests._async.conftest import AsyncDummyUnitOfWork, DummyModel, MyMetadata


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


async def test_collect_new_events(
    uow: AsyncDummyUnitOfWork, foo_factory: type[DummyModel]
):
    foo = foo_factory(id="1", counter=0)
    foo.messages.append(FooCreated(id="1"))
    bar = foo_factory(id="1", counter=0)
    bar.messages.append(BarCreated())
    foo2 = foo_factory(id="2", counter=0)
    foo2.messages.append(FooCreated(id="2"))

    async with uow as tuow:
        await tuow.foos.add(foo)
        await tuow.bars.add(bar)
        await tuow.foos.add(foo2)
        await tuow.commit()

    iter = uow.collect_new_events()
    assert next(iter) == FooCreated(id="1")
    assert next(iter) == FooCreated(id="2")
    assert next(iter) == BarCreated()
    with pytest.raises(StopIteration):
        next(iter)


async def test_transaction_rollback_on_error(uow: AsyncDummyUnitOfWork):
    tuow = None
    try:
        async with uow as tuow:
            raise ValueError("Boom")
    except Exception:
        ...
    assert tuow is not None
    assert tuow.status == TransactionStatus.rolledback


async def test_transaction_rollback_explicit_commit(uow: AsyncDummyUnitOfWork):
    with pytest.raises(TransactionError) as ctx:
        async with uow as tuow:
            tuow.foos  # noqa B018

    assert str(ctx.value).endswith(
        "Transaction must be explicitly close. Missing commit/rollback call."
    )


async def test_transaction_invalid_state(uow: AsyncDummyUnitOfWork):
    with pytest.raises(TransactionError) as ctx:
        async with uow as tuow:
            tuow.status = TransactionStatus.closed

    assert str(ctx.value).endswith("Transaction is closed.")


async def test_transaction_invalid_usage(uow: AsyncDummyUnitOfWork):
    with pytest.raises(TransactionError) as ctx:
        transaction = AsyncUnitOfWorkTransaction(uow)
        transaction.status = TransactionStatus.committed
        async with transaction:
            ...

    assert str(ctx.value).endswith("Invalid transaction status.")


async def test_transaction_commit_after_rollback(uow: AsyncDummyUnitOfWork):
    with pytest.raises(TransactionError) as ctx:
        async with uow as tuow:
            await tuow.rollback()
            await tuow.commit()

    assert str(ctx.value).endswith("Transaction already closed (rolledback).")


async def test_transaction_commit_twice(uow: AsyncDummyUnitOfWork):
    with pytest.raises(TransactionError) as ctx:
        async with uow as tuow:
            await tuow.commit()
            await tuow.commit()

    assert str(ctx.value).endswith("Transaction already closed (committed).")


async def test_detach_transaction(uow: AsyncDummyUnitOfWork):
    async with uow as tuow:
        await uow.foos.add(DummyModel(id="1", counter=1))
        await uow.foos.add(DummyModel(id="2", counter=1))
        await uow.foos.add(DummyModel(id="3", counter=1))
        await tuow.commit()

    async with uow as tuow:
        iter_foos = uow.foos.find(id="2")
        await tuow.detach()

    try:
        foos = [foo async for foo in iter_foos]
        assert foos == [DummyModel(id="2", counter=1)]
    finally:
        await tuow.close()
