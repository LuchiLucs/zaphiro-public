from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import Engine
from db.config import settings

# NOTE: using a dict to store the singleton engine but can be hot-swapped, e.g. testing
_engine_container: dict[str, Engine] = {"engine": None}


def get_engine():
    if _engine_container["engine"] is None:
        # This will use whatever URI is currently set in config
        _engine_container["engine"] = create_engine(
            settings.URI, connect_args={"check_same_thread": False}
        )
    return _engine_container["engine"]


def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session


def reset_engine():
    _engine_container["engine"] = None


def create_db_and_tables():
    SQLModel.metadata.create_all(get_engine())
