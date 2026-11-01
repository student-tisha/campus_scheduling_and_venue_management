from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User

DEMO_USERS = [
    {"email": "admin@cit.edu", "password": "Admin@123",
     "name": "Dean's Office (Admin)", "role": "admin"},
    {"email": "coordinator@cit.edu", "password": "Coord@123",
     "name": "CSE Department Coordinator", "role": "department_coordinator",
     "department": "CSE"},
    {"email": "faculty@cit.edu", "password": "Faculty@123",
     "name": "Dr. Ananya Mishra", "role": "faculty",
     "faculty_id": "F01", "department": "CSE"},
    {"email": "club@cit.edu", "password": "Club@123",
     "name": "Robotics Club Representative", "role": "club",
     "club_name": "Robotics Club"},
]


def seed_users(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(User)) > 0:
        return
    for u in DEMO_USERS:
        db.add(User(
            email=u["email"], name=u["name"], role=u["role"],
            department=u.get("department"), faculty_id=u.get("faculty_id"),
            club_name=u.get("club_name"),
            password_hash=hash_password(u["password"]),
        ))
    db.commit()
