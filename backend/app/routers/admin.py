from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database import get_db
from app.models import User
from app.services import dataset_loader as loader
from app.services import generation, store

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset")
def reset_demo_data(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    """Back to a clean state: dataset reloaded, timetable/exams/bookings/changes wiped."""
    counts = loader.load_dataset(db)
    store.clear_all(db)
    return {"reset": True, "counts": counts}


@router.post("/generate")
def generate_all(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return generation.generate_all(db)


@router.post("/generate/timetable")
def generate_timetable(db: Session = Depends(get_db),
                       user: User = Depends(require_roles("admin"))):
    return generation.generate_timetable(db)


@router.post("/generate/exams")
def generate_exams(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return generation.generate_exams(db)
