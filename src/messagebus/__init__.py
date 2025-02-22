"""
messagebus API.
"""

from importlib.metadata import version

from pydantic import Field

from .domain.model import (
    Command,
    Event,
    GenericCommand,
    GenericEvent,
    GenericModel,
    Message,
    Metadata,
    Model,
    TMetadata,
)
from .service._async.dependency import AsyncDependency
from .service._async.eventstream import (
    AsyncAbstractEventstreamTransport,
    AsyncEventstreamPublisher,
    AsyncSinkholeEventstreamTransport,
)
from .service._async.registry import AsyncMessageBus, async_listen
from .service._async.repository import AsyncAbstractRepository
from .service._async.unit_of_work import (
    AsyncAbstractUnitOfWork,
    AsyncEventstoreAbstractRepository,
    AsyncSinkholeEventstoreRepository,
    AsyncUnitOfWorkTransaction,
)
from .service._sync.dependency import SyncDependency
from .service._sync.eventstream import (
    SyncAbstractEventstreamTransport,
    SyncEventstreamPublisher,
    SyncSinkholeEventstreamTransport,
)
from .service._sync.registry import SyncMessageBus, sync_listen
from .service._sync.repository import SyncAbstractRepository
from .service._sync.unit_of_work import (
    SyncAbstractUnitOfWork,
    SyncEventstoreAbstractRepository,
    SyncSinkholeEventstoreRepository,
    SyncUnitOfWorkTransaction,
)
from .service.eventstream import AbstractMessageSerializer

__version__ = version("messagebus")

__all__ = [
    # Eventstream
    "AbstractMessageSerializer",
    "AsyncAbstractEventstreamTransport",
    # Repository
    "AsyncAbstractRepository",
    # Unit of work
    "AsyncAbstractUnitOfWork",
    "AsyncEventstoreAbstractRepository",
    "AsyncEventstreamPublisher",
    "AsyncMessageBus",
    "AsyncSinkholeEventstoreRepository",
    "AsyncSinkholeEventstreamTransport",
    "AsyncUnitOfWorkTransaction",
    "Command",
    "Event",
    "Field",
    # models
    "GenericCommand",
    "GenericEvent",
    "GenericModel",
    "Message",
    "TMetadata",
    "Metadata",
    "Model",
    "SyncAbstractEventstreamTransport",
    "SyncAbstractRepository",
    "SyncAbstractUnitOfWork",
    "SyncEventstoreAbstractRepository",
    "SyncEventstreamPublisher",
    "SyncMessageBus",
    "SyncSinkholeEventstoreRepository",
    "SyncSinkholeEventstreamTransport",
    "SyncUnitOfWorkTransaction",
    # Registry
    "async_listen",
    "sync_listen",
    # Dependencies,
    "AsyncDependency",
    "SyncDependency",
]
