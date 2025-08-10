
from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, full_name=user.full_name, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def mark_attendance(db: Session, student_id: int):
    db_attendance = models.Attendance(student_id=student_id)
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def set_user_otp_secret(db: Session, user_id: int, secret: str):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.otp_secret = secret
        db.commit()
        db.refresh(db_user)
    return db_user
