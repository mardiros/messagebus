import abc
from collections.abc import Mapping, Sequence
from typing import Any, Generic

from messagebus.domain.model.message import TMessage
from messagebus.service._async.unit_of_work import TAsyncUow
from messagebus.typing import AsyncMessageHandler, P


class MissingDependencyError(RuntimeError):
    """Raised if a dependency has not been added in the bus or in the handle command."""


class AsyncDependency(abc.ABC):
    """Describe an async dependency"""

    @abc.abstractmethod
    async def on_after_commit(self) -> None:
        """Method called when the unit of work transaction is has been commited."""

    @abc.abstractmethod
    async def on_after_rollback(self) -> None:
        """Method called when the unit of work transaction is has been rolled back."""


class AsyncMessageHook(Generic[TMessage, TAsyncUow, P]):
    callback: AsyncMessageHandler[TMessage, "TAsyncUow", P]
    dependencies: Sequence[str]
    optional_dependencies: Sequence[str]

    def __init__(
        self,
        callback: AsyncMessageHandler[TMessage, "TAsyncUow", P],
        dependencies: Sequence[str],
        optional_dependencies: Sequence[str],
    ) -> None:
        self.callback = callback
        self.dependencies = dependencies
        self.optional_dependencies = optional_dependencies

    async def __call__(
        self,
        msg: TMessage,
        uow: "TAsyncUow",
        dependencies: Mapping[str, AsyncDependency],
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
        resp = await self.callback(msg, uow, **deps)  # type: ignore
        return resp
