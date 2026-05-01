from sqlmodel import SQLModel, create_engine, Session
engine = create_engine("sqlite:///exam_system.db", echo=False, connect_args={"check_same_thread": False})
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session
