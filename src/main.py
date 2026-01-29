from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from core.utils import get_logger
from db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# setup logger
logger = get_logger("app", "DEBUG")

# setup app
app = FastAPI(
    title="Zaphiro Technologies",
    summary="Zaphiro Technologies - API to manage a power grid model (Python)",
    root_path="/b",
    version="PoC",
    lifespan=lifespan,
)

# add routes
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    kwargs = {"app": app, "host": "127.0.0.1", "port": 8080}
    uvicorn.run(**kwargs)
