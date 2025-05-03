Eventstream With Celery
=======================

In the :ref:`chapter 6<cookbook chapter 6>`, we discover how the messagebus library handle eventstream.
We've implement an :class:`messagebus.AsyncAbstractEventstreamTransport` in order
to send events to a stream.

We've done a fake implementation, sending to a python list, it's time to give
a try using the popular library Celery_.

.. _Celery: https://docs.celeryq.dev/en/stable/


Start by installing the latest celery version, celery 5 at the moment, and
we are going to celery pytest fixtures too, so we can install it now.


.. important::

    Because the library is thin as possible, in term of code and dependencies, the
    messagebus library does not comes with an implementation, the present documentation
    can be reproduce and adapted.

::

    $ poetry add celery[pytest]

we will create a new :term:`adapter` in ``src/reading_club/adapters/eventstream.py``
and we will do a sub testing direcectory in order to reuse all the main fixtures
from our main conftest, but override the ``transport`` to tests our new one.



Lets write a test in ``tests/eventstream_celery/conftest.py``

.. literalinclude:: 10_sending_eventstream_using_celery_01.py

The tests here follow the `celery doc`_. It use the ``celery_app`` and ``celery_worker``
fixtures from the pytest-celery package.

.. _`celery doc`: https://docs.celeryq.dev/en/stable/userguide/testing.html#pytest

and our implementation in ``src/reading_club/adapters/eventstream.py``

.. literalinclude:: 10_sending_eventstream_using_celery_02.py

Note that Celery does not support asyncio at the moment, so we run the tasks in an
executor.


::

    $ poetry run pytest -sxv
    ========================== test session starts ==========================
    collected 11 items

    tests/test_service_handler_add_book.py::test_register_book[ok] PASSED
    tests/test_service_handler_add_book.py::test_register_book[integrity error] PASSED
    tests/test_service_handler_add_book.py::test_bus_handler PASSED
    tests/eventstream_celery/test_adapter.py::test_eventstream PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_ok PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_err[params0] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return a known book] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return an error] PASSED
    tests/uow_sqla/test_repositories.py::test_messagestore_add PASSED
    tests/uow_sqla/test_transaction.py::test_commit PASSED
    tests/uow_sqla/test_transaction.py::test_rollback PASSED
    ========================== 11 passed in 4.37s ===========================

The tests pass, but it is terribly slow.

So we can keep it like this, or maybe write more code in order to tests what we are
responsible for.

Actually, we don't need to tests that a worker can retrieve our message, we've tested
it once, and it works, we probably kept that kind of tests in a functional tests suite,
but now, we will just ensure we can send a task using a celery fake object.

Lets write our own fixtures.

.. literalinclude:: 10_sending_eventstream_using_celery_03.py

We've create a fake celery class, that just implementing the API things we consume,
and a fixture ``celery_queue`` which will receive the tasks we want to track that
are sent.

.. literalinclude:: 10_sending_eventstream_using_celery_04.py

We adapt our tests to ensure that the message in the ``celery_queue`` fixture
has been tracked.

Lets run our test.

::

    $ poetry run pytest -sxv
    ========================== test session starts ==========================
    collected 11 items

    tests/test_service_handler_add_book.py::test_register_book[ok] PASSED
    tests/test_service_handler_add_book.py::test_register_book[integrity error] PASSED
    tests/test_service_handler_add_book.py::test_bus_handler PASSED
    tests/eventstream_celery/test_adapter.py::test_eventstream PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_ok PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_err[params0] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return a known book] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return an error] PASSED
    tests/uow_sqla/test_repositories.py::test_messagestore_add PASSED
    tests/uow_sqla/test_transaction.py::test_commit PASSED
    tests/uow_sqla/test_transaction.py::test_rollback PASSED

    ========================== 11 passed in 0.30s ===========================

The test suite is now fast again.


.. note::

    The ``Celery.send_task`` method is used to generate a signature without having
    a Celery task created.
    In real life, the Celery used here just require the correct broker, routing,
    and serialization directive. Says differently, only celery configuration is
    required, not code.
