==========
messagebus
==========

.. image:: https://github.com/mardiros/messagebus/actions/workflows/publish-doc.yml/badge.svg
   :target: https://mardiros.github.io/messagebus/
   :alt: Doc

.. image:: https://github.com/mardiros/messagebus/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/mardiros/messagebus/actions/workflows/tests.yml
   :alt: Continuous Integration

.. image:: https://codecov.io/gh/mardiros/messagebus/branch/main/graph/badge.svg?token=BKUM2G3YSR
   :target: https://codecov.io/gh/mardiros/messagebus
   :alt: Coverage Report


messagebus is a library crafted for sending messages on a bus, providing foundational classes
for event-driven development and Domain-Driven Design.

It includes a comprehensive registration system that utilizes decorators and handlers
to dispatch events effectively.

messagebus is used for internal messaging inside a python program, but also,
with external services that can consume messages throw an event stream,
where message can be published to a given transport.

messagebus supports both asynchronous operations using async/await and a synchronous API.

.. note::
    The synchronous API is generated by unasync from the asynchronous api.
