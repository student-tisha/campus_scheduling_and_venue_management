from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import (admin, ai, auth, bookings, changes, dashboard, dataset, explain,
                         export, health, timetable)
from app.services import dataset_loader
from app.services.user_seed import seed_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if not dataset_loader.is_loaded(db):
            dataset_loader.load_dataset(db)
        seed_users(db)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.frontend_origin.split(",") if o.strip()]
    + ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dataset.router)
app.include_router(timetable.router)
app.include_router(export.router)
app.include_router(bookings.router)
app.include_router(changes.router)
app.include_router(ai.router)
app.include_router(explain.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
