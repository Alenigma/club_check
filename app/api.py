
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import crud, schemas, models
from .database import SessionLocal, engine
from typing import List
import pyotp
from datetime import timedelta

# This is insecure, replace with a real secret key management
SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

api_router = APIRouter()

# Create a user
@api_router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

# Get all users (for teacher)
@api_router.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Manual attendance marking
@api_router.post("/attendance/manual", response_model=schemas.Attendance)
def manual_attendance(attendance: schemas.ManualAttendance, db: Session = Depends(get_db)):
    # Here you should add logic to check if the user making the request is a teacher
    return crud.mark_attendance(db=db, student_id=attendance.student_id)

# Generate QR token for a student
@api_router.get("/student/qr-token/{user_id}")
def get_student_qr_token(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.otp_secret:
        secret = pyotp.random_base32()
        crud.set_user_otp_secret(db, user_id, secret)
        user.otp_secret = secret

    totp = pyotp.TOTP(user.otp_secret)
    return {"token": totp.now(), "expires_in": 30}

# Scan student's QR code
@api_router.post("/attendance/scan-student")
def scan_student_qr(token: str, db: Session = Depends(get_db)):
    # In a real app, you'd need to find which user this token belongs to.
    # This is a simplified example. We'd need to iterate over users.
    # This is inefficient and should be improved in a real system.
    users = crud.get_users(db)
    for user in users:
        if user.otp_secret:
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(token):
                crud.mark_attendance(db, student_id=user.id)
                return {"message": f"Attendance marked for {user.full_name}"}
    
    raise HTTPException(status_code=400, detail="Invalid or expired token")
