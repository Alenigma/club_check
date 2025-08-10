
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import crud, schemas, models
from .database import SessionLocal
from typing import List
import pyotp
import uuid
from datetime import timedelta, datetime
from .dependencies import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    require_roles,
    get_current_user,
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

api_router = APIRouter()

# --- Auth ---

@api_router.post("/auth/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@api_router.post("/auth/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "uid": user.id, "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.get("/attendance/count")
def get_attendance_count(
    section_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["student", "teacher"])),
):
    # student sees own count, teacher can pass ?user_id to see student's count
    user_id = current_user.id
    return {"count": crud.count_section_attendance(db, student_id=user_id, section_id=section_id)}

# Create a user
@api_router.post("/users/", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

# Get all users (for teacher)
@api_router.get("/users/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Manual attendance marking (per section)
@api_router.post("/attendance/manual", response_model=schemas.SectionAttendance)
def manual_attendance(
    attendance: schemas.ManualAttendance,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    if not crud.is_teacher_in_section(db, section_id=attendance.section_id, teacher_id=current_user.id):
        raise HTTPException(status_code=403, detail="Teacher not assigned to this section")
    if not crud.is_student_in_section(db, section_id=attendance.section_id, student_id=attendance.student_id):
        raise HTTPException(status_code=400, detail="Student not in section")
    return crud.mark_section_attendance(db=db, section_id=attendance.section_id, student_id=attendance.student_id)

# Generate QR token for a student
@api_router.get("/student/qr-token/{user_id}")
def get_student_qr_token(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role != "teacher" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not user.otp_secret:
        secret = pyotp.random_base32()
        crud.set_user_otp_secret(db, user_id, secret)
        user.otp_secret = secret

    totp = pyotp.TOTP(user.otp_secret)
    return {"token": totp.now(), "expires_in": 30}

# Scan student's QR code (per section)
@api_router.post("/attendance/scan-student", response_model=schemas.SectionAttendance)
def scan_student_qr(
    token: str,
    section_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    # In a real app, you'd need to find which user this token belongs to.
    users = crud.get_users(db)
    for user in users:
        if user.otp_secret:
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(token):
                if not crud.is_teacher_in_section(db, section_id=section_id, teacher_id=current_user.id):
                    raise HTTPException(status_code=403, detail="Teacher not assigned to this section")
                if not crud.is_student_in_section(db, section_id=section_id, student_id=user.id):
                    raise HTTPException(status_code=400, detail="Student not in section")
                return crud.mark_section_attendance(db, section_id=section_id, student_id=user.id)

    raise HTTPException(status_code=400, detail="Invalid or expired token")

# --- Master QR Code for Teachers ---

@api_router.post("/teacher/master-qr/enable/{teacher_id}")
def enable_master_qr(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    teacher = crud.get_user(db, teacher_id)
    if not teacher or teacher.role != 'teacher':
        raise HTTPException(status_code=404, detail="Teacher not found")
    if current_user.id != teacher_id:
        raise HTTPException(status_code=403, detail="You can only enable your own master QR")
    
    new_secret = str(uuid.uuid4())
    crud.update_master_qr_mode(db, teacher_id, True, new_secret)
    return {"message": "Master QR mode enabled", "master_qr_secret": new_secret}

@api_router.post("/teacher/master-qr/disable/{teacher_id}")
def disable_master_qr(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    teacher = crud.get_user(db, teacher_id)
    if not teacher or teacher.role != 'teacher':
        raise HTTPException(status_code=404, detail="Teacher not found")
    if current_user.id != teacher_id:
        raise HTTPException(status_code=403, detail="You can only disable your own master QR")

    crud.update_master_qr_mode(db, teacher_id, False, None)
    return {"message": "Master QR mode disabled"}

@api_router.post("/attendance/scan-lecture")
def scan_lecture_qr(
    secret: str,
    student_id: int,
    section_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["student"])),
):
    # Find teacher by secret and ensure student belongs to the section
    teacher = crud.find_teacher_by_master_secret(db, secret)
    if not teacher:
        raise HTTPException(status_code=400, detail="Invalid or inactive Master QR code")

    if not crud.is_student_in_section(db, section_id=section_id, student_id=student_id):
        raise HTTPException(status_code=400, detail="Student not in section")

    crud.mark_section_attendance(db, section_id=section_id, student_id=student_id)
    return {"message": f"Attendance marked by master QR from {teacher.full_name}"}


# --- Sections ---

@api_router.post("/sections", response_model=schemas.Section)
def create_section(
    section: schemas.SectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    return crud.create_section(db, section)


@api_router.get("/sections", response_model=List[schemas.Section])
def list_sections(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.list_sections(db)


@api_router.post("/sections/{section_id}/students/{student_id}")
def add_student_to_section(
    section_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    user = crud.get_user(db, student_id)
    if not user or user.role != 'student':
        raise HTTPException(status_code=404, detail="Student not found")
    crud.add_student_to_section(db, section_id, student_id)
    return {"message": "Student added to section"}


@api_router.post("/sections/{section_id}/teachers/{teacher_id}")
def add_teacher_to_section(
    section_id: int,
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles(["teacher"])),
):
    user = crud.get_user(db, teacher_id)
    if not user or user.role != 'teacher':
        raise HTTPException(status_code=404, detail="Teacher not found")
    crud.add_teacher_to_section(db, section_id, teacher_id)
    return {"message": "Teacher added to section"}


