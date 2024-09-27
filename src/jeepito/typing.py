"""
Propagate commands and events to every registered handles.

"""
import logging
from typing import Any, Callable, Coroutine, TypeVar

from jeepito.domain.model import Message

from .service._async.unit_of_work import AsyncAbstractUnitOfWork
from .service._sync.unit_of_work import SyncAbstractUnitOfWork

log = logging.getLogger(__name__)

TAsyncUow = TypeVar("TAsyncUow", bound=AsyncAbstractUnitOfWork[Any])
TSyncUow = TypeVar("TSyncUow", bound=SyncAbstractUnitOfWork[Any])
TMessage = TypeVar("TMessage", bound=Message)

AsyncMessageHandler = Callable[[TMessage, TAsyncUow], Coroutine[Any, Any, Any]]
SyncMessageHandler = Callable[[TMessage, TSyncUow], Any]
