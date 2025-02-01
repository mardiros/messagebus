from typing import Any

from messagebus.service._async.registry import async_listen
from messagebus.service._async.unit_of_work import AsyncAbstractUnitOfWork
from tests._async.conftest import (
    AnotherDummyCommand,
    DummyCommand,
    DummyEvent,
    Notifier,
)


@async_listen
async def handler(command: DummyCommand, uow: AsyncAbstractUnitOfWork[Any]): ...


@async_listen
async def handler_evt1(command: DummyEvent, uow: AsyncAbstractUnitOfWork[Any]): ...


@async_listen
async def handler_evt2(command: DummyEvent, uow: AsyncAbstractUnitOfWork[Any]): ...


@async_listen
async def handler_with_dependency_injection(
    command: AnotherDummyCommand,
    uow: AsyncAbstractUnitOfWork[Any],
    notifier: Notifier,
): ...
