from sqlmodel import SQLModel, Session, create_engine
import os

DB_DIR = os.environ.get("DB_DIR", os.path.join(os.path.dirname(__file__), "../data"))
os.makedirs(DB_DIR, exist_ok=True)
DB_URL = f"sqlite:///{os.path.join(DB_DIR, 'urls.db')}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session