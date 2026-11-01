from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.services import dataset_loader as loader
from app.services import assistant
from app.services.booking_parser import parse_request
from app.services.llm import llm_available

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ParseIn(BaseModel):
    text: str


@router.get("/status")
def status(user: User = Depends(get_current_user)):
    return {"llm_available": llm_available(),
            "note": "If false, the parser uses built-in rules. Manual forms always work."}


@router.post("/parse-booking")
def parse_booking(body: ParseIn, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    return parse_request(body.text, loader.get_data_dict(db), user.role)


class AssistantIn(BaseModel):
    message: str
    faculty_id: str | None = None


@router.post("/assistant")
def faculty_assistant(body: AssistantIn, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    return assistant.handle(db, user, body.message, body.faculty_id)
