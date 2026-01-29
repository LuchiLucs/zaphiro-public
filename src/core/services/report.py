# REF: https://docs.pola.rs/user-guide/io/database/#difference-between-read_database_uri-and-read_database
# NOTE: Note that pl.read_database_uri is likely to be faster than pl.read_database if you are using a SQLAlchemy or DBAPI2 connection as these connections may load the data row-wise into Python before copying the data again to the column-wise Apache Arrow format.

# REF: https://fastapi.tiangolo.com/advanced/advanced-dependencies/#background-tasks-and-dependencies-with-yield-technical-details
import polars as pl
from datetime import datetime
from db.models import ReportDB
from core.models import FinalReportSchema, ComponentType
from core.utils import get_logger, timer
from sqlmodel import create_engine, text
from db.config import settings
from sqlmodel import Session

logger = get_logger("app", "DEBUG")


class ReportService:
    def __init__(self):
        self.engine = create_engine(
            settings.URI, connect_args={"check_same_thread": False}
        )

    @property
    def db_uri(self):
        return f"{self.engine.url.render_as_string(hide_password=False)}"

    @timer
    def run_report_task(self, report_id: int, start_date: datetime, end_date: datetime):
        """Entry point for the background task."""
        try:
            # 1. EXTRACT
            df = self._extract_data(start_date, end_date)

            if df.is_empty():
                self._update_db_status(report_id, "completed", None)
                return

            # 2. TRANSFORM (Domain Logic)
            # We convert to lazy immediately to allow Polars to optimize
            report_domain_model = self._transform_to_kpis(df.lazy())

            # 3. LOAD
            self._update_db_status(report_id, "completed", report_domain_model)
        except Exception as e:
            logger.error(f"Task {report_id} failed: {e}", exc_info=True)
            self._update_db_status(report_id, f"failed: {str(e)}", None)
        finally:
            self.engine.dispose()

    @timer
    def _extract_data(self, start: datetime, end: datetime) -> pl.DataFrame:
        """I/O Layer: Purely responsible for getting data out of SQLite."""
        start_str = start.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end.strftime('%Y-%m-%d %H:%M:%S')
        query = f"""
            SELECT m.component_id, m.value, m.measurement_type, m.timestamp,
                   c.component_type, c.voltage_kv, c.capacity_mva, c.length_km
            FROM measurements m
            JOIN components c ON m.component_id = c.id
            WHERE m.timestamp BETWEEN '{start_str}' AND '{end_str}'
        """
        # NOTE: DOES NOT work
        # TODO: SQLAlchemy and SQLModel differs in the exec/execution
        #       Polars read_database uses SQLAlchemy support
        #       There may be incompatibles integration
        # stmt = (
        #     select(
        #         MeasurementDB.component_id,
        #         MeasurementDB.value,
        #         MeasurementDB.measurement_type,
        #         MeasurementDB.timestamp,
        #         ComponentDB.component_type,
        #         ComponentDB.voltage_kv,
        #         ComponentDB.capacity_mva,
        #         ComponentDB.length_km,
        #     )
        #     .join(ComponentDB)
        #     .where(
        #         and_(
        #             MeasurementDB.timestamp >= start,
        #             MeasurementDB.timestamp <= end,
        #         )
        #     )
        # )
        # return pl.read_database(query=text(query), connection=self.session)

        # NOTE: works
        logger.debug(f"Report service extracting from db URI: {self.db_uri}")
        df = pl.read_database_uri(query=query, uri=self.db_uri, engine="adbc")

        # NOTE: works
        # df = pl.read_database(query=text(query), connection=self.engine)

        logger.info(f"Extraction complete. Rows: {df.height}, Columns: {df.width}")
        return df

    @timer
    def _transform_to_kpis(self, ldf: pl.LazyFrame) -> FinalReportSchema:
        """
        Domain Layer: Pure transformation logic.
        Takes a LazyFrame, returns a Pydantic Domain Model.
        """
        # Schema Normalization
        schema = ldf.collect_schema()
        logger.debug(f"Extracted schema: {schema}")

        # Check the type using the collected schema
        if schema["timestamp"] == pl.String:
            ldf = ldf.with_columns(pl.col("timestamp").str.to_datetime())

        # Logic for unique components (metadata)
        unique_ldf = ldf.unique(subset=["component_id"])

        # Define the computations (Lazy)
        count_by_type = unique_ldf.group_by("component_type").agg(
            pl.len().alias("count")
        )

        trans_cap = (
            unique_ldf.filter(
                pl.col("component_type") == ComponentType.TRANSFORMER.value
            )
            .group_by("voltage_kv")
            .agg(pl.col("capacity_mva").sum().alias("total_capacity_mva"))
        )

        line_len = (
            unique_ldf.filter(pl.col("component_type") == ComponentType.LINE.value)
            .group_by("voltage_kv")
            .agg(pl.col("length_km").sum().alias("total_length_km"))
        )

        daily_avg = (
            ldf.with_columns(pl.col("timestamp").dt.truncate("1d").alias("day"))
            .group_by(["day", "measurement_type", "component_type"])
            .agg(pl.col("value").mean().alias("avg_value"))
            .sort(["day", "component_type"])
        )

        # COLLECT: One single execution for all computations
        # Polars runs these in parallel where possible
        results = pl.collect_all([count_by_type, trans_cap, line_len, daily_avg])

        # Map back to Domain Model
        return FinalReportSchema(
            summary={
                "components_by_type": results[0].to_dicts(),
                "transformer_capacity_by_voltage": results[1].to_dicts(),
                "line_length_by_voltage": results[2].to_dicts(),
            },
            daily_averages=results[3]
            .with_columns(pl.col("day").dt.to_string("%Y-%m-%d"))
            .to_dicts(),
        )

    @timer
    def _update_db_status(
        self, report_id: int, status: str, report: FinalReportSchema | None
    ):
        """Storage Layer: Persistence logic."""
        logger.debug(f"Report Service updating to db: {self.engine.url}")
        with Session(self.engine) as session:
            db_report = session.get(ReportDB, report_id)
            if db_report:
                db_report.status = status
                if report:
                    db_report.result_json = report.model_dump_json()
                session.add(db_report)
                session.commit()
