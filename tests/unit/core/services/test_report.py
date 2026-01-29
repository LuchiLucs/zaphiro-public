import polars as pl
from core.services.report import ReportService
from core.models import ComponentType
from core.models import FinalReportSchema, TransformerCapacity, DailyAverage


def test_transform_to_kpis_logic():
    # Create minimal mock data in memory
    mock_data = pl.DataFrame(
        {
            "component_id": [1, 1, 2],
            "value": [10.0, 20.0, 100.0],
            "measurement_type": ["voltage", "voltage", "current"],
            "timestamp": [
                "2026-01-01T10:00:00",
                "2026-01-01T11:00:00",
                "2026-01-01T12:00:00",
            ],
            "component_type": [
                ComponentType.TRANSFORMER.value,
                ComponentType.TRANSFORMER.value,
                ComponentType.LINE.value,
            ],
            "voltage_kv": [110.0, 110.0, 220.0],
            "capacity_mva": [63.0, 63.0, None],
            "length_km": [None, None, 42.5],
        }
    ).lazy()

    # Initialize service
    service = ReportService()

    # Run only the transformation logic
    report: FinalReportSchema = service._transform_to_kpis(mock_data)

    # Verify the business logic (the DDD part)
    # KPI 1: Unique counts
    counts = {
        item.component_type: item.count for item in report.summary.components_by_type
    }
    assert (
        counts[ComponentType.TRANSFORMER.value] == 1
    )  # Should NOT be 2, despite 2 measurement rows
    assert counts[ComponentType.LINE.value] == 1

    # KPI 2 and 3: Capacity
    trans_cap = report.summary.transformer_capacity_by_voltage[0]
    assert trans_cap == TransformerCapacity(voltage_kv=110.0, total_capacity_mva=63.0)

    # KPI 4: Daily Averages
    # NOTE: sorted by day and component type
    daily_avg_truth = [
        DailyAverage(
            day="2026-01-01",
            measurement_type="current",
            component_type=ComponentType.LINE.value,
            avg_value=100.0,
        ),
        DailyAverage(
            day="2026-01-01",
            measurement_type="voltage",
            component_type=ComponentType.TRANSFORMER.value,
            avg_value=15.0,
        ),
    ]
    assert daily_avg_truth == report.daily_averages
