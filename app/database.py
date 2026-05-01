import os
from sqlmodel import SQLModel, create_engine, Session

# ياخذ من Railway (Postgres) وإذا ما فيه يرجع SQLite محلي
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///exam_system.db")

# إعدادات حسب نوع قاعدة البيانات
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL (Railway)
    engine = create_engine(
        DATABASE_URL,
        echo=False
    )


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
