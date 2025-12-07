0.15.1  - Released on 2025-12-07
--------------------------------
* Makes prometheus-client optional.
* Imports changed (breaking change).

0.15.0  - Released on 2025-12-07
--------------------------------
* The message store created_at is not timezone aware, and in UTC (breaking change).
* Typing API updated to get a TUnitOfWork instead of all of its parameters in the transaction type (breaking change).
* The metrics store class can be specified, it is a generic now.

0.14.0  - Released on 2025-12-07
--------------------------------
* Implement a metrics store in the unit of work.
* Expose metrics in prometheus registry by default.

0.13.0  - Released on 2025-05-03
--------------------------------
* Breaking Change: eventstore property has been rename messagestore in the unit of work.
* Typing Update: now the unit of work have a new generic parameter to specify the class
  of the messagestore. Now more methods can be safely added to the messagestore.
* TransactionStatus type is exposed in the API.

0.12.0  - Released on 2025-04-13
--------------------------------
* Add a new state for the transaction for streaming context.

0.11.1  - Released on 2025-03-01
--------------------------------
* Customize repr to improve tests unit equality debugging
* Fix bug in model equality, they must have the same type

0.11.0  - Released on 2025-02-23
--------------------------------
* Add support of optional dependencies.
  if a service handlers use a dependency with a default value,
  then the message bus handle it properly.

0.10.0  - Released on 2025-02-22
--------------------------------
* Add support of transient dependencies.
  Now, bus.handle accept kwargs that are dependencies that can
  be consumed by handlers

0.9.0  - Released on 2025-02-13
-------------------------------
* Change the depencendies injection in event handlers (api break!)
  Now, an instance of a class is created on every bus.handle call.
  It lets isolate depenencies per unit of work transaction.

0.8.1  - Released on 2025-02-01
-------------------------------
* Fix CI

0.8.0  - Released on 2025-02-01
-------------------------------
* Starts implementing depencencies injected in event handlers
* Drop python 3.9 support

0.7.0  - Released on 2024-11-28
-------------------------------
* Always exclude messages while dumping models

0.6.0  - Released on 2024-11-15
-------------------------------
* First version of messagebus, previously named jeepito
