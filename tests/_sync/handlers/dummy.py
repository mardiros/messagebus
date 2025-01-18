from typing import Any, ClassVar

from messagebus.service._sync.registry import sync_listen
from messagebus.service._sync.unit_of_work import SyncAbstractUnitOfWork
from tests._sync.conftest import AnotherDummyCommand, DummyCommand, DummyEvent


class Notifier:
    inbox: ClassVar[list[str]] = []

    def send_message(self, message: str):
        self.inbox.append(message)


@sync_listen
def handler(command: DummyCommand, uow: SyncAbstractUnitOfWork[Any]): ...


@sync_listen
def handler_evt1(command: DummyEvent, uow: SyncAbstractUnitOfWork[Any]): ...


@sync_listen
def handler_evt2(command: DummyEvent, uow: SyncAbstractUnitOfWork[Any]): ...


@sync_listen
def handler_with_dependency_injection(
    command: AnotherDummyCommand,
    uow: SyncAbstractUnitOfWork[Any],
    notifier: Notifier,
): ...
