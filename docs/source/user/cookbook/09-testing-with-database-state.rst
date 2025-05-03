Testing with database state
===========================

Many times, for testing, we need to have data in a database to tests how
function behave on them. This is usually done by setting up an application
database with fixtures.

The main problem of that is that when we alter the database schema,
fixtures must be updated. On the other way, if the database state is
based on passed commands, then, this problem disappear.

Now lets update our tests in order to initialize a database state using fixtures.

So lets add this fixture in our main conftest file (``tests/conftest.py``).

.. literalinclude:: 09_testing_with_database_state_01.py

This fixture is dead simple, it is a parametrized fixtures, that consume a
parameter params, which is a dict that contains a list of commands to be play
by the bus.

This initialize the database using all the registered service handler, without
any database details. Those service handler must be properly tests rights, to
get the proper database state but you are probably aware of that.

Not that this fixture does not revert its changes after the test execution.
This is not necessary because we create a new state from scratch on every tests
in order to ensure that every tests are fully isolated.

lets rewrite and parametrized our tests that are should.

.. literalinclude:: 09_testing_with_database_state_02.py


Now lets run our tests

::

    $ poetry run pytest -sxv
    ========================== test session starts ==========================
    collected 9 items

    tests/test_service_handler_add_book.py::test_register_book[params0] PASSED
    tests/test_service_handler_add_book.py::test_bus_handler PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_ok PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_err[params0] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return a known book] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return an error] PASSED
    tests/uow_sqla/test_repositories.py::test_messagestore_add PASSED
    tests/uow_sqla/test_transaction.py::test_commit PASSED
    tests/uow_sqla/test_transaction.py::test_rollback PASSED
    =========================== 9 passed in 0.48s ===========================


.. note::

    You may notice that the tests run slower than before, which was predictible.
    But this is quite acceptable.
    By the way, using an in memory unit of work and the time saved by having
    maintainable fixture is what matter the most.


Now, lets rewrite another test from the chapter 4 where we have two tests in one.
We have our new fixture that could be used here to get the database state and get
our two test runned sequently.


Here is the context, from the file ``test_service_handler_add_book.py``

.. literalinclude:: 04_service_handler_02.py

Lets rewrite it with our new fixture:

.. literalinclude:: 09_testing_with_database_state_03.py


Run our tests

::

    $ poetry run pytest -sxv
    ========================== test session starts ==========================
    collected 10 items

    tests/test_service_handler_add_book.py::test_register_book[ok] PASSED
    tests/test_service_handler_add_book.py::test_register_book[integrity error] PASSED
    tests/test_service_handler_add_book.py::test_bus_handler PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_ok PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_err[params0] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return a known book] PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id[return an error] PASSED
    tests/uow_sqla/test_repositories.py::test_messagestore_add PASSED
    tests/uow_sqla/test_transaction.py::test_commit PASSED
    tests/uow_sqla/test_transaction.py::test_rollback PASSED
    ========================== 10 passed in 0.48s ===========================


.. note::

    When you have more than one parametrized tests, this is important to use the
    `pytest.param` function and set an id. Fixtures becomes longer than tests, and
    may be refactor for clarity as well. From my point of view, at the moment,
    it is acceptable like this.
