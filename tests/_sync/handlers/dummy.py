from typing import Any

from messagebus.service._sync.registry import sync_listen
from messagebus.service._sync.unit_of_work import SyncAbstractUnitOfWork
from tests._sync.conftest import Notifier
from tests.conftest import AnotherDummyCommand, DummyCommand, DummyEvent


@sync_listen
def handler(command: DummyCommand, uow: SyncAbstractUnitOfWork[Any, Any]): ...


@sync_listen
def handler_evt1(command: DummyEvent, uow: SyncAbstractUnitOfWork[Any, Any]): ...


@sync_listen
def handler_evt2(command: DummyEvent, uow: SyncAbstractUnitOfWork[Any, Any]): ...


@sync_listen
def handler_with_dependency_injection(
    command: AnotherDummyCommand,
    uow: SyncAbstractUnitOfWork[Any, Any],
    notifier: Notifier,
): ...
