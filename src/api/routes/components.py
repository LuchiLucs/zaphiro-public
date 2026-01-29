from fastapi import APIRouter, HTTPException, status, Query
from api.schemas.component import ComponentResponse, ComponentCreate, ComponentUpdate
from db.models import ComponentDB
from sqlalchemy.exc import IntegrityError
from api.dependencies import SessionDep
from core.models import ComponentType
from sqlmodel import select, col
from api.dependencies import ManagerDep

router = APIRouter(prefix="/components", tags=["components"])


@router.post(
    "",
    response_model=ComponentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[ManagerDep],
)
def create_component(
    component_data: ComponentCreate,
    db: SessionDep,
) -> ComponentResponse:
    """
    Create a new component with automatic type discovery.

    Accessible by: manager role only.
    """
    # 1. Map Pydantic model to SQLAlchemy model
    db_component = ComponentDB(**component_data.model_dump())

    # 2. Persist to Database
    try:
        db.add(db_component)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A component with this name and substation already exists.",
        )

    # 3. Return polymorphic response
    return db_component


@router.put("/{id}", response_model=ComponentResponse, dependencies=[ManagerDep])
def update_component(
    id: int,
    update_data: ComponentUpdate,
    db: SessionDep,
) -> ComponentResponse:
    """
    Strict PUT: Replaces the component and allows type-switching (not a PATCH)

    Accessible by: manager role only.
    """

    # 1. Retrieve the existing record from the DB identity map
    db_component = db.get(ComponentDB, id)
    if not db_component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Component {id} not found"
        )

    # 2. Extract the update data (includes component_type and specific fields)
    update_dict = update_data.model_dump()

    # 3. Clean Sweep: Reset type-specific fields to None
    # This prevents 'Line' data from sticking around if converting to a 'Transformer'
    type_fields = ["capacity_mva", "length_km", "voltage_kv", "status"]
    for field in type_fields:
        setattr(db_component, field, None)

    # 4. Apply new values
    for key, value in update_dict.items():
        setattr(db_component, key, value)

    # 5. Persist
    try:
        db.add(db_component)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A component with this name/substation already exists.",
        )
    return db_component


@router.delete(
    "/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[ManagerDep]
)
def delete_component(
    id: int,
    db: SessionDep,
) -> None:
    """
    Delete a component and all its associated measurements.

    Returns 204 No Content on success.
    """
    # 1. Fetch the existing record
    db_component = db.get(ComponentDB, id)

    # 2. If it doesn't exist, raise 404
    if not db_component:
        raise HTTPException(
            # NOTE: we could return HTTP_204_NO_CONTENT for idempotency
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component with ID {id} not found",
        )

    # 3. Perform the deletion
    # Because of cascade_delete=True in the model,
    # SQLAlchemy/SQLModel will handle the measurements table cleanup.
    db.delete(db_component)
    db.commit()

    # 4. Return No Content
    return None


@router.get("", response_model=list[ComponentResponse])
def list_components(
    db: SessionDep,
    name_search: str | None = Query(None, description="Search by partial name"),
    substation: str | None = Query(None, description="Filter by substation"),
    component_type: ComponentType | None = Query(None, description="Filter by type"),
    limit: int | None = Query(100, ge=1, le=1000, description="Set to null for all"),
    offset: int = Query(0, ge=0),
) -> list[ComponentDB]:
    """
    Retrieve components with search, filtering, and pagination.
    If limit is omitted, returns default batch.
    """
    statement = select(ComponentDB)

    if name_search:
        statement = statement.where(col(ComponentDB.name).contains(name_search))

    if substation:
        statement = statement.where(ComponentDB.substation == substation)

    if component_type:
        statement = statement.where(ComponentDB.component_type == component_type)

    if limit is not None:
        statement = statement.offset(offset).limit(limit)

    return list(db.exec(statement).all())
