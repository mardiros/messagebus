from sqlalchemy import JSON, Column, DateTime, Index, MetaData, String, Table, Uuid

metadata = MetaData()


books = Table(
    "books",
    metadata,
    Column("id", Uuid(), nullable=False, primary_key=True),
    Column("title", String, nullable=False),
    Column("author", String, nullable=False),
    Column("isbn", String(20), nullable=False),
    Index("idx_books_isbn", "isbn", unique=True),
)


messages = Table(
    "messages",
    metadata,
    Column("id", Uuid(), nullable=False, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("metadata", JSON(), nullable=False),
    Column("payload", JSON(), nullable=False),
    Index("idx_messages_created_at", "created_at"),
)
