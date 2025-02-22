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
