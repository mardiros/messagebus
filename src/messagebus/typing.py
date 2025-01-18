"""
Propagate commands and events to every registered handles.

"""

import logging
from collections.abc import Callable, Coroutine
from typing import Any, Concatenate, ParamSpec, TypeVar

from messagebus.domain.model import Message

from .service._async.unit_of_work import AsyncAbstractUnitOfWork
from .service._sync.unit_of_work import SyncAbstractUnitOfWork

log = logging.getLogger(__name__)

P = ParamSpec("P")

TAsyncUow = TypeVar("TAsyncUow", bound=AsyncAbstractUnitOfWork[Any])
TSyncUow = TypeVar("TSyncUow", bound=SyncAbstractUnitOfWork[Any])
TMessage = TypeVar("TMessage", bound=Message[Any])

AsyncMessageHandler = Callable[
    Concatenate[TMessage, TAsyncUow, P], Coroutine[Any, Any, Any]
]
SyncMessageHandler = Callable[Concatenate[TMessage, TSyncUow, P], Any]
