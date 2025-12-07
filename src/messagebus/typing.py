"""
Propagate commands and events to every registered handles.

"""

from collections.abc import Callable, Coroutine
from typing import Any, Concatenate, ParamSpec, TypeVar

from messagebus.domain.model import Message

from .service._async.unit_of_work import AsyncAbstractUnitOfWork, TAsyncUow
from .service._sync.unit_of_work import SyncAbstractUnitOfWork, TSyncUow

P = ParamSpec("P")

TMessage = TypeVar("TMessage", bound=Message[Any])

AsyncMessageHandler = Callable[
    Concatenate[TMessage, TAsyncUow, P], Coroutine[Any, Any, Any]
]
SyncMessageHandler = Callable[Concatenate[TMessage, TSyncUow, P], Any]


__all__ = [
    "AsyncAbstractUnitOfWork",
    "TAsyncUow",
    "SyncAbstractUnitOfWork",
    "TSyncUow",
    "TMessage",
    "AsyncMessageHandler",
    "SyncMessageHandler",
]
