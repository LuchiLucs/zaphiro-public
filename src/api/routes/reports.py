from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from core.services.report import ReportService
from sqlmodel import select, col
import json

from api.schemas.report import ReportRequest, ReportResponse, ReportDetailResponse
from api.dependencies import SessionDep
from db.models import ReportDB
from api.dependencies import ManagerDep

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{id}", response_model=ReportDetailResponse)
def get_report(id: int, db: SessionDep):
    """
    Get the specific results of a report

    Accessible by all users
    """
    db_report = db.get(ReportDB, id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    if db_report.status != "completed" or db_report.result_json is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Report is not ready yet"
            )

    report = db_report.model_dump()
    report["result_json"] = json.loads(report["result_json"])
    return report


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[ManagerDep],
)
def create_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: SessionDep,
) -> ReportDB:
    """
    Generate a report asynchronously

    Accessible by manager only

    Returns the report metadata immediately while Polars works in the background.
    """
    # 1. Create the database record to track progress
    new_report = ReportDB(
        start_date=request.start_date,
        end_date=request.end_date,
        status="pending",
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # 2. Exploit the service to run Polars in a background thread
    report_service = ReportService()
    background_tasks.add_task(
        report_service.run_report_task,
        new_report.id,
        request.start_date,
        request.end_date,
    )
    return new_report


@router.get("", response_model=list[ReportResponse])
def list_reports(db: SessionDep) -> list[ReportDB]:
    """
    List all available reports

    Accessible by all users
    """
    statement = select(ReportDB).order_by(col(ReportDB.id).desc())
    return list(db.exec(statement).all())
