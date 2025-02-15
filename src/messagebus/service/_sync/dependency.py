import abc
from collections.abc import Mapping, Sequence
from typing import Any, Generic

from messagebus.domain.model.message import TMessage
from messagebus.service._sync.unit_of_work import TSyncUow
from messagebus.typing import P, SyncMessageHandler


class SyncDependency(abc.ABC):
    """Describe an async dependency"""

    @abc.abstractmethod
    def on_after_commit(self) -> None:
        """Method called when the unit of work transaction is has been commited."""

    @abc.abstractmethod
    def on_after_rollback(self) -> None:
        """Method called when the unit of work transaction is has been rolled back."""


class SyncMessageHook(Generic[TMessage, TSyncUow, P]):
    callback: SyncMessageHandler[TMessage, "TSyncUow", P]
    dependencies: Sequence[str]

    def __init__(
        self,
        callback: SyncMessageHandler[TMessage, "TSyncUow", P],
        dependencies: Sequence[str],
    ) -> None:
        self.callback = callback
        self.dependencies = dependencies

    def __call__(
        self,
        msg: TMessage,
        uow: "TSyncUow",
        dependencies: Mapping[str, SyncDependency],
    ) -> Any:
        deps = {k: dependencies[k] for k in self.dependencies}
        resp = self.callback(msg, uow, **deps)  # type: ignore
        return resp
