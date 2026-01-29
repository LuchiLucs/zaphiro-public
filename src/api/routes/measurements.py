from fastapi import APIRouter, HTTPException, status
from api.schemas.measurement import MeasurementCreate, MeasurementResponse
from db.models import MeasurementDB, ComponentDB
from api.dependencies import SessionDep
from sqlalchemy.exc import IntegrityError
from api.dependencies import ManagerDep

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.post(
    "",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ManagerDep],
)
def add_measurement(
    measurement_data: MeasurementCreate,
    db: SessionDep,
) -> MeasurementResponse:
    """
    Add a new measurement reading to a specific component.

    Accessible by: manager role only.
    """
    # 1. Verify the parent component exists
    component = db.get(ComponentDB, measurement_data.component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component with ID {measurement_data.component_id} not found.",
        )

    # 2. Map Pydantic model to SQLModel
    db_measurement = MeasurementDB(**measurement_data.model_dump())

    # 3. Persist to Database
    try:
        db.add(db_measurement)
        db.commit()
        return db_measurement
    except IntegrityError:
        db.rollback()
        # NOTE: we could return HTTP_200_OK to be "silent" about sensor duplicates
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Measurement already exists for this timestamp and type.",
        )
