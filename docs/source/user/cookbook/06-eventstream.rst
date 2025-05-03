.. _`cookbook chapter 6`:

Event stream
============

When a command has been processed by a service hook, then, an event
can be sent to a stream of event in order to get some pub/sub synchronization,
and also to get an obvervable architecture.

This is particulary usefull in a microservice architecture.

First, we have to define an event format.

In our example, when a book has been registered, we can raises the following
event.

.. literalinclude:: 06_eventstream_01.py
   :emphasize-lines: 12

The event is a message, and, we can append the message of the book during the
registration hook. The unit of work will process the message and send it to
the event stream because the flagged ``published`` is set to ``True``.

.. note::

    Commands and Events can be published.
    It is preferable to publish all events and avoid the publication of commands.
    The reason is that when a message is public, then it has to be maintained and
    avoid any breaking changes. By the way, when a new version of a message is added,
    then, the service that rely on it has to be updated too. And preferably before
    coming to production.
    This is why commands may bot be published, and processed using the message bus.


We can update our unit test that our message are sent to a transport backend,
represented by the fixture transport.

.. literalinclude:: 06_eventstream_02.py
   :emphasize-lines: 13,28-36


At that moment, have to implement the transport in our conftest.py file

.. literalinclude:: 06_eventstream_03.py
   :emphasize-lines: 23,61-63,82-84,88-89

First, we create an Eventstream Transport that store messages in a list, and expose it
as a fixture. The transport is also configured to override the ``messagestore`` property
of the unit of work. We reuse the ``AsyncSinkholeMessageStoreRepository`` repository.
which means that we don't store the events locally, but, we set up our transport,
having the effect of sending published events to the eventstream.

Now lets update the code of the service handler to raise the event:

.. literalinclude:: 06_eventstream_04.py
   :emphasize-lines: 15-17

Note that we add the message to be processed by the message bus in the service handler,
not in a repository. In the real world, we have multiple implementation of our unit of
work and this code can't be added anytime we create a repository implementation.
The messaging part for the bus are handled by the service layers.

Lastly, note that our initial test ``test_register_book`` can also be updated to test
that the unit of work will received the message before processing it.
This tests directly call the message bus handler and bypass the bus.

.. literalinclude:: 06_eventstream_05.py
