from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.services import explain as svc

router = APIRouter(prefix="/api/explain", tags=["explain"])


class AskIn(BaseModel):
    question: str


@router.post("/ask")
def ask(body: AskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return svc.ask(db, user, body.question)


@router.get("/session/{sid}")
def session(sid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = svc.explain_session(db, sid)
    if not res:
        raise HTTPException(404, "Session not found")
    text, source = svc.friendly(res["facts"])
    return {**res, "explanation": text, "source": source}


@router.get("/booking/{rid}")
def booking(rid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = svc.explain_booking(db, rid, user)
    if not res:
        raise HTTPException(404, "Booking request not found")
    text, source = svc.friendly(res["facts"])
    return {**res, "explanation": text, "source": source}


@router.get("/change/{pid}")
def change(pid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = svc.explain_change(db, pid, user)
    if not res:
        raise HTTPException(404, "Change request not found")
    text, source = svc.friendly(res["facts"])
    return {**res, "explanation": text, "source": source}
