from fastapi import APIRouter

from . import components, measurements, reports
import auth.routes
from api.dependencies import UserDep

router = APIRouter()
router.include_router(auth.routes.router)
# NOTE: make all the APIs private with at least the "user" scope
router.include_router(components.router, dependencies=[UserDep])
router.include_router(measurements.router, dependencies=[UserDep])
router.include_router(reports.router, dependencies=[UserDep])
