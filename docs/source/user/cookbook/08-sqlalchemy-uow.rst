Unit Of Work using SQLAlchemy
=============================

Now that we have a finally modelized our application, we can start
storing data in a storage backend.
For the example, we will use the latestest version of SQLAlchemy, which
is SQLAlchemy 2 at the moment.

We will use sqlite in memory for testing purpose.

::

    poetry add "sqlalchemy[mypy]" aiosqlite


.. note::

    we install the mypy extentions here, even if we don't check mypy tests in our
    example.

Create the sql schema
---------------------

Actually, we are not going to use `SQLAlchemy ORM`_, because we are going
to map our models directly, and because we don't needs layers of abstraction,
only the `SQLAlchemy Core`_ is enough for our use case.

The repository pattern will implement the traditional ORM part that you usually use,
but as a primary goals, we don't wan't any database implementation details in our
core domaine model, this is why we don't use SQLAlchemy ORM at all.

We will create all this code in an ``adapters`` (see :term:`Adapter`),
and create a submodul ``uow_sqla``

::

    mkdir -p src/reading_club/adapters/uow_sqla
    touch src/reading_club/adapters/__init__.py
    touch src/reading_club/adapters/uow_sqla/__init__.py
    touch src/reading_club/adapters/uow_sqla/orm.py
    touch src/reading_club/adapters/uow_sqla/uow.py

Lets create our sql schema now.

In the ``reading_club.adapters.uow_sqla.orm`` module, we will create the database
schema using the `SQLAlchemy Core`_:

.. literalinclude:: 08_sqlalchemy_uow_01.py

We will see how we map that later, before continue, lets write some
tests for our unit of work.

.. _`SQLAlchemy ORM`: https://docs.sqlalchemy.org/en/20/orm/
.. _`SQLAlchemy Core`: https://docs.sqlalchemy.org/en/20/core/


.. note::

    I avoid the stub of ``reading_club.adapters.uow_sqla.uow`` for the moment,
    we will get the proper implementation after the tests in order to get this
    page shorter.

Testing the unit of work
------------------------

First, We are going to separate our sql tests from others tests,
in order to get a conftest that override the ``tests/conftest.py``
but we also ensure to not use sql in the rest of the tests.
Then, we have to implement the :meth:`messagebus.AsyncAbstractUnitOfWork.commit`
and :meth:`messagebus.AsyncAbstractUnitOfWork.rollback` and we have to write transaction
tests to ensure it works.

::

    mkdir tests/uow_sqla
    touch tests/uow_sqla/__init__.py
    touch tests/uow_sqla/conftest.py
    touch tests/uow_sqla/test_transaction.py


Now, lets write the tests in ``uow_sqla/test_transaction.py``

.. literalinclude:: 08_sqlalchemy_uow_03.py

Both tests are really similar, they insert a book, using the uow sql connection,
in the books table, when we commit, we ensure the book is stored, when we rollback,
we ensure the book is not present.


The tests needs some sql fixture we can already provide in ``uow_sqla/conftest.py``

.. literalinclude:: 08_sqlalchemy_uow_02.py

we have an engine to bind an in memory database containing our schema, and that
can be passed to the Unit Of Work, and a session, to retrieve data from the database,
used in the tests expectation.

We have all we need, it's time to start our implementation.

Create the sql unit of work
---------------------------

In the ``reading_club.adapters.uow_sqla.uow`` module, we will start writing
our unit of work.

.. literalinclude:: 08_sqlalchemy_uow_04.py

We have implement our unit of work and declare all our repositories without implementing
them. We explicitly raise NotImplementedError to get our repositories instanciable.

If we run our tests now:

::

    $ poetry run pytest -sxv
    ========================== test session starts ==========================
    collected 4 items

    tests/test_service_handler_add_book.py::test_register_book PASSED
    tests/test_service_handler_add_book.py::test_bus_handler PASSED
    tests/uow_sqla/test_transaction.py::test_commit PASSED
    tests/uow_sqla/test_transaction.py::test_rollback PASSED
    =========================== 4 passed in 0.04s ===========================

Implement the book repository
-----------------------------

We can start with a couple of tests for the Ok and the Error cases in a
``test_repositories.py`` file.

.. literalinclude:: 08_sqlalchemy_uow_05.py
   :emphasize-lines: 14,20,23,41,46

We can see that those tests expect that:
* the add method will return Ok(...) if its works
* the stored book saved correspont to what the model contains
* the seen attribute, is set to let the message bus consume the book messages.
* integrity error does not raise but are stored in a Err().
* the seen attribute does not contains models that can't be stored in the repository.

We also see that those new fixtures are required in our ``uow_sqla/conftest.py``:

.. literalinclude:: 08_sqlalchemy_uow_06.py

Finally the add method implemented using SQLAlchemy

.. literalinclude:: 08_sqlalchemy_uow_07.py

The tests suite should pass.

::

    $ poetry run pytest -sxv
    ========================== test session starts ==========================
    collected 6 items

    tests/test_service_handler_add_book.py::test_register_book PASSED
    tests/test_service_handler_add_book.py::test_bus_handler PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_ok PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_err PASSED
    tests/uow_sqla/test_transaction.py::test_commit PASSED
    tests/uow_sqla/test_transaction.py::test_rollback PASSED
    =========================== 4 passed in 0.04s ===========================


Lets continue with the ``by_id`` implementation.

here is our test

.. literalinclude:: 08_sqlalchemy_uow_08.py

..note::

    you can see that our tests are a bit ugly, the initialization of the tests
    is made inside the tests not in our fixtures.
    Don't be afraid, we will improve that in the next chapter.

And our implmenetation

.. literalinclude:: 08_sqlalchemy_uow_09.py
   :emphasize-lines: 31-37

Implement the event repository
------------------------------

Before implementing the ``BookRepository.by_id`` we will take the time to implement
our event repository in order to get our bus working, which will be usefull to
create books using the message bus directly in our fixtures.


our new tests  in``test_repositories.py``:

.. literalinclude:: 08_sqlalchemy_uow_10.py

And our implementation.

.. literalinclude:: 08_sqlalchemy_uow_11.py

There is no much to say here, it take the message and store in in the table.
Because the messagebus does not rely on results, it does not return a Result object,
our implementation raise exceptions if it does not works.


Before closing this chapter, lets run our tests and conclude

::

    $ poetry run pytest -sxv
    ========================== test session starts ==========================
    collected 9 items

    tests/test_service_handler_add_book.py::test_register_book PASSED
    tests/test_service_handler_add_book.py::test_bus_handler PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_ok PASSED
    tests/uow_sqla/test_repositories.py::test_book_add_err PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id_ok PASSED
    tests/uow_sqla/test_repositories.py::test_book_by_id_err PASSED
    tests/uow_sqla/test_repositories.py::test_messagestore_add PASSED
    tests/uow_sqla/test_transaction.py::test_commit PASSED
    tests/uow_sqla/test_transaction.py::test_rollback PASSED
    =========================== 9 passed in 0.43s ===========================


At the moment, our book review model contains the book registration, with commands
and events used by the messagebus.

But, we have some tests that are not clean, the ``test_book_add_err`` that initialize
its tests inside them, which will not scale, and more for the ``test_book_by_id_ok``,
we retrieve a book, but we only have one book here, so, we cannot be sure that it
is the proper book that could be retrieve in real life.

This is the subject of the next chapter.
