import abc
from collections.abc import Mapping, Sequence
from typing import Any, Generic

from messagebus.domain.model.message import TMessage
from messagebus.service._sync.unit_of_work import TSyncUow
from messagebus.typing import P, SyncMessageHandler


class MissingDependencyError(RuntimeError):
    """Raised if a dependency has not been added in the bus or in the handle command."""


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
    optional_dependencies: Sequence[str]

    def __init__(
        self,
        callback: SyncMessageHandler[TMessage, "TSyncUow", P],
        dependencies: Sequence[str],
        optional_dependencies: Sequence[str],
    ) -> None:
        self.callback = callback
        self.dependencies = dependencies
        self.optional_dependencies = optional_dependencies

    def __call__(
        self,
        msg: TMessage,
        uow: "TSyncUow",
        dependencies: Mapping[str, SyncDependency],
    ) -> Any:
        try:
            deps = {k: dependencies[k] for k in self.dependencies}
        except KeyError as key:
            raise MissingDependencyError(
                f"Missing messagebus dependency {key}"
            ) from None
        deps.update(
            {
                k: dependencies[k]
                for k in self.optional_dependencies
                if k in dependencies
            }
        )
        resp = self.callback(msg, uow, **deps)  # type: ignore
        return resp
