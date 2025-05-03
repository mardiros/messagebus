from pathlib import Path

import unasync

unasync.unasync_files(
    [str(p) for p in Path("src/messagebus/service/_async").iterdir() if p.is_file()],
    rules=[
        unasync.Rule(
            "src/messagebus/service/_async",
            "src/messagebus/service/_sync",
            additional_replacements={
                "_async": "_sync",
                "TAsyncUow": "TSyncUow",
                "TAsyncMessageStore": "TSyncMessageStore",
                "async_listen": "sync_listen",
            },
        ),
    ],
)

unasync.unasync_files(
    [str(p) for p in Path("tests/_async").iterdir() if p.is_file()],
    rules=[
        unasync.Rule(
            "tests/_async",
            "tests/_sync",
            additional_replacements={
                "_async": "_sync",
                "tests._async.handlers": "tests._sync.handlers",
            },
        ),
    ],
)


unasync.unasync_files(
    [str(p) for p in Path("tests/_async/handlers").iterdir() if p.is_file()],
    rules=[
        unasync.Rule(
            "tests/_async/handlers",
            "tests/_sync/handlers",
            additional_replacements={
                "_async": "_sync",
                "async_listen": "sync_listen",
            },
        ),
    ],
)
