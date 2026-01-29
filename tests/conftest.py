
import os
import pytest
import polars as pl
from datetime import timedelta
from sqlmodel import Session, SQLModel, create_engine, select, insert, func
from sqlmodel.pool import StaticPool
from db import get_session
from db.config import settings
from db.models import ComponentDB, MeasurementDB
from main import app
from core.utils import get_logger
from datetime import UTC, datetime
from httpx import ASGITransport, AsyncClient

logger = get_logger("app_test", "DEBUG")


# Override the settings object directly after import
# TODO: in-memory to be fixed when connecting with Polars
# NOTE: early override to change db.settings before app is imported
# DB_URI = "sqlite:///:memory:"
# DB_URI = "sqlite:///database_performance.db"
os.environ["DB_URI"] = "sqlite:///test_database.db"
settings.URI = os.environ["DB_URI"]

NUM_COMPONENTS = 100
NUM_MEASUREMENTS = 300

@pytest.fixture(name="session")
def session_fixture():
    """
    REF: https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#memory-database
    REF: https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    Fixture to create a testing engine based on SQLAlchemy/SQLModel

    Using database
    based on the testing enviroment
    """
    engine = create_engine(
        settings.URI, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    logger.info(f"Creating testing database engine: {engine.url}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        populate_components(session)
        populate_measurements(session)
        yield session

    # Cleanup after all tests
    engine.dispose()
    db_path = settings.URI.replace("sqlite:///", "")
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Removed test database: {db_path}")


@pytest.fixture(name="client")
async def client_fixture(session: Session):
    """
    REF: https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#client-fixture
    Fixture to create a testing client based on our FastAPI app

    Use FastAPI dependency_overrides to change the dependencies injected
    based on the testing enviroment
    """
    logger.info("Creating testing FastAPI client...")

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


def populate_components(session):
    logger.info(f"Adding {NUM_COMPONENTS} components...")

    # Define the variations
    configs = {
        0: {
            "type": "TRANSFORMER",
            "prefix": "TR",
            "extra": {"voltage_kv": 110.0, "capacity_mva": 63.0},
        },
        1: {
            "type": "LINE",
            "prefix": "LN",
            "extra": {"voltage_kv": 220.0, "length_km": 42.5},
        },
        2: {"type": "SWITCH", "prefix": "SW", "extra": {"status": "CLOSED"}},
    }

    # Creating the data
    components = [
        ComponentDB(
            id=i,
            name=f"{configs[i % 3]['prefix']}_{i:03d}",
            substation=f"SUB_{i % 5}",
            component_type=configs[i % 3]["type"],
            **configs[i % 3]["extra"],
        )
        for i in range(1, NUM_COMPONENTS + 1)
    ]

    session.add_all(components)
    session.commit()


def populate_measurements(session):
    logger.info(f"Adding {NUM_MEASUREMENTS * 3} measurements per component...")
    df_len = NUM_COMPONENTS * NUM_MEASUREMENTS * 3

    # Define dimensions
    comp_ids = pl.int_range(1, NUM_COMPONENTS + 1, eager=True).alias("component_id")
    m_types = pl.Series("measurement_type", ["CURRENT", "VOLTAGE", "POWER"])
    start_dt = datetime(2026, 1, 1, tzinfo=UTC)
    interval_str = "15s"
    end_dt = start_dt + timedelta(seconds=15 * (NUM_MEASUREMENTS - 1))
    time_index = pl.datetime_range(
        start=start_dt, end=end_dt, interval=interval_str, eager=True
    ).alias("timestamp")

    # Cross join to guarantee UniqueConstraint compliance
    # This creates a row for every combination of (Comp x Time x Type)
    df = (
        comp_ids.to_frame()
        .join(time_index.to_frame(), how="cross")
        .join(m_types.to_frame(), how="cross")
    )

    # Creating values
    df = df.with_columns(
        pl.int_range(0, 1000, 1)
        .sample(n=len(df), with_replacement=True, seed=42)
        .alias("value")
    )

    # Bridge between Polars and the Session of SQLAlchemy
    dicts = df.to_dicts()

    # TODO: SQLAlchemy Bulk Insert: faster than session.add_all() ?
    logger.info(f"Bulk inserting {df_len} records via SQLAlchemy...")
    session.execute(insert(MeasurementDB), dicts)
    session.commit()

    # Check counts
    comp_count = session.exec(select(func.count(ComponentDB.id))).one()
    meas_count = session.exec(select(func.count(MeasurementDB.id))).one()

    logger.info(
        f"VERIFICATION: {comp_count} components and {meas_count} measurements in DB."
    )
    assert comp_count == NUM_COMPONENTS
    assert meas_count == (
        NUM_COMPONENTS * NUM_MEASUREMENTS * 3
    )  # x3 because of your 3 types
    # TODO: bypass SQLAlchemy and use low-level adbc driver of Polars
    # TODO: faster because native C/Rust bulk-insert implementations?
    # TODO: what about the memory space used, is it shared?
    # TODO: what about thread/async/process concurrency?
    # sqlmodel_uri = session.bind.url
    # adbc_uri = sqlmodel_uri.split() + ":memory:"
    # logger.info(f"Bulk writing {df_len} rows to {adbc_uri}...")

    # df.write_database(
    #     table_name="measurements",
    #     connection=adbc_uri,
    #     if_table_exists="append",
    #     engine="adbc"
    # )
