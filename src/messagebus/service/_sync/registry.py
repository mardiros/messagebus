"""
Propagate commands and events to every registered handles.

"""

import importlib
import inspect
import logging
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, Generic, cast

import venusian  # type: ignore

from messagebus.domain.model import GenericCommand, GenericEvent, Message
from messagebus.domain.model.message import TMessage
from messagebus.service._sync.dependency import (
    P,
    SyncDependency,
    SyncMessageHandler,
    SyncMessageHook,
)
from messagebus.service._sync.unit_of_work import (
    SyncUnitOfWorkTransaction,
    TRepositories,
    TSyncUow,
)

log = logging.getLogger(__name__)
VENUSIAN_CATEGORY = "messagebus"


class ConfigurationError(RuntimeError):
    """Prevents bad usage of the add_listener."""


def sync_listen(
    wrapped: SyncMessageHandler[TMessage, TSyncUow, P],
) -> SyncMessageHandler[TMessage, TSyncUow, P]:
    """
    Decorator to listen for a command or an event.

    Note that you can handle one listener for a command, and many for events.
    The command handler result is returned by the handle call of the message bus.
    """

    def callback(
        scanner: venusian.Scanner,
        name: str,
        ob: SyncMessageHandler[TMessage, TSyncUow, P],
    ) -> None:
        if not hasattr(scanner, VENUSIAN_CATEGORY):
            return  # coverage: ignore
        argsspec = inspect.getfullargspec(ob)
        msg_type = argsspec.annotations[argsspec.args[0]]
        scanner.messagebus.add_listener(msg_type, wrapped)  # type: ignore

    venusian.attach(wrapped, callback, category=VENUSIAN_CATEGORY)  # type: ignore
    return wrapped


class SyncMessageBus(Generic[TRepositories]):
    """Store all the handlers for commands an events."""

    def __init__(self, **dependencies: Any) -> None:
        self.commands_registry: dict[
            type[GenericCommand[Any]], SyncMessageHook[Any, Any, Any]
        ] = {}
        self.events_registry: dict[
            type[GenericEvent[Any]], list[SyncMessageHook[Any, Any, Any]]
        ] = defaultdict(list)
        self.dependencies = cast(Mapping[str, type[SyncDependency]], dependencies or {})

    def add_listener(
        self, msg_type: type[Message[Any]], callback: SyncMessageHandler[Any, Any, P]
    ) -> None:
        signature = inspect.signature(callback)
        dependencies: list[str] = []
        optional_dependencies: list[str] = []
        for idx, (key, value) in enumerate(signature.parameters.items()):
            if idx >= 2:
                # if key not in self.dependencies:
                #     raise ConfigurationError(
                #         f"Missing dependency in message bus: {key} for command "
                #         f"type {msg_type.__name__}, listener: {callback.__name__}"
                #     )
                if value.default is value.empty:
                    dependencies.append(key)
                else:
                    optional_dependencies.append(key)

        msghook = SyncMessageHook(callback, dependencies, optional_dependencies)
        if issubclass(msg_type, GenericCommand):
            if msg_type in self.commands_registry:
                raise ConfigurationError(
                    f"{msg_type} command has been registered twice"
                )
            self.commands_registry[msg_type] = msghook
        elif issubclass(msg_type, GenericEvent):
            self.events_registry[msg_type].append(msghook)
        else:
            raise ConfigurationError(
                f"Invalid usage of the listen decorator: "
                f"type {msg_type} should be a command or an event"
            )

    def remove_listener(
        self, msg_type: type, callback: SyncMessageHandler[Any, Any, P]
    ) -> None:
        if issubclass(msg_type, GenericCommand):
            if msg_type not in self.commands_registry:
                raise ConfigurationError(f"{msg_type} command has not been registered")
            del self.commands_registry[msg_type]
        elif issubclass(msg_type, GenericEvent):
            msg_hooks = [
                v for v in self.events_registry[msg_type] if v.callback == callback
            ]
            if msg_hooks:
                self.events_registry[msg_type].remove(msg_hooks[0])
            else:
                raise ConfigurationError(f"{msg_type} event has not been registered")
        else:
            raise ConfigurationError(
                f"Invalid usage of the listen decorator: "
                f"type {msg_type} should be a command or an event"
            )

    def handle(
        self,
        command: GenericCommand[Any],
        uow: SyncUnitOfWorkTransaction[TRepositories],
        **transient_dependencies: Any,
    ) -> Any:
        """
        Notify listener of that event registered with `messagebus.add_listener`.
        Return the first event from the command.

        :param message: The message to handle, should be a command.
        """
        dependencies = {k: uow.add_listener(v()) for k, v in self.dependencies.items()}
        if transient_dependencies:
            [uow.add_listener(d) for d in transient_dependencies.values()]
            dependencies.update(transient_dependencies)
        queue: list[Message[Any]] = [command]
        idx = 0
        ret = None
        while queue:
            message = queue.pop(0)
            if not isinstance(message, GenericCommand | GenericEvent):
                raise RuntimeError(f"{message} was not an Event or Command")
            msg_type = type(message)
            if msg_type in self.commands_registry:
                cmdret = self.commands_registry[msg_type](  # type: ignore
                    cast(GenericCommand[Any], message), uow, dependencies
                )
                if idx == 0:
                    ret = cmdret
                queue.extend(uow.uow.collect_new_events())
            elif msg_type in self.events_registry:
                for msghook in self.events_registry[msg_type]:  # type: ignore
                    msghook(cast(GenericEvent[Any], message), uow, dependencies)
                    queue.extend(uow.uow.collect_new_events())
            uow.eventstore.add(message)
            idx += 1
        return ret

    def scan(
        self,
        *mods: str,
    ) -> None:
        """
        Scan the module (or modules) containing service handlers.

        when a message is handled by the bus, the bus propagate the message
        to hook functions, called :term:`Service Handler` that receive the message,
        and a :term:`Unit Of Work` to process it has a business transaction.
        """
        scanner = venusian.Scanner(messagebus=self)
        for modname in mods:
            if modname.startswith("."):
                raise ValueError(
                    f"scan error: relative package unsupported for {modname}"
                )
            mod = importlib.import_module(modname)
            scanner.scan(mod, categories=[VENUSIAN_CATEGORY])  # type: ignore
