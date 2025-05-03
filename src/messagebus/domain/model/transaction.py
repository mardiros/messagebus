"""Transaction models."""

import enum


class TransactionError(RuntimeError):
    """A runtime error raised if the transaction lifetime is inappropriate."""


class TransactionStatus(enum.Enum):
    """Transaction status used to ensure transaction lifetime."""

    running = "running"
    """Initial state of the transaction status in the context manager."""
    rolledback = "rolledback"
    """state of the transaction status after it has been aborted."""
    committed = "committed"
    """state of the transaction status after it has been committed."""
    closed = "closed"
    """state of the transaction status after the with state block."""
    streaming = "streaming"
    """
    Unsafe way to manually exit the transaction manager for streaming purpose.

    While streaming response in some context like FastAPI or Starlette
    StreamingResponse, the transaction must be closed lately, usually in a
    finally block to close the transaction.
    """
