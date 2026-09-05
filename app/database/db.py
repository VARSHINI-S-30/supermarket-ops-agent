from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = "sqlite:///./data/supermarket.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# SQLITE WRITE LOCK
# ============================================================

def begin_write_transaction(db):
    """
    Start an SQLite IMMEDIATE transaction.

    This obtains a write reservation before business data
    is modified, helping serialize competing inventory/billing
    writes and preventing stock corruption.
    """

    db.execute(
        text("BEGIN IMMEDIATE")
    )