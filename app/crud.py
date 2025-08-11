
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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

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

def update_master_qr_mode(db: Session, teacher_id: int, enabled: bool, secret: str = None):
    db_teacher = get_user(db, teacher_id)
    if db_teacher and db_teacher.role == 'teacher':
        db_teacher.master_qr_mode_enabled = enabled
        db_teacher.master_qr_secret = secret
        db.commit()
        db.refresh(db_teacher)
    return db_teacher


def create_section(db: Session, section: schemas.SectionCreate):
    db_section = models.Section(name=section.name)
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section
def list_sections(db: Session):
    return db.query(models.Section).all()
def add_student_to_section(db: Session, section_id: int, student_id: int):
    db_link = models.SectionStudent(section_id=section_id, student_id=student_id)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link
def add_teacher_to_section(db: Session, section_id: int, teacher_id: int):
    db_link = models.SectionTeacher(section_id=section_id, teacher_id=teacher_id)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link
def mark_section_attendance(db: Session, section_id: int, student_id: int):
    db_attendance = models.SectionAttendance(section_id=section_id, student_id=student_id)
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance
def find_teacher_by_master_secret(db: Session, secret: str):
    return (
        db.query(models.User)
        .filter(models.User.role == 'teacher')
        .filter(models.User.master_qr_mode_enabled == True)
        .filter(models.User.master_qr_secret == secret)
        .first()
    )
def is_student_in_section(db: Session, section_id: int, student_id: int) -> bool:
    return (
        db.query(models.SectionStudent)
        .filter(models.SectionStudent.section_id == section_id)
        .filter(models.SectionStudent.student_id == student_id)
        .first()
        is not None
    )
def is_teacher_in_section(db: Session, section_id: int, teacher_id: int) -> bool:
    return (
        db.query(models.SectionTeacher)
        .filter(models.SectionTeacher.section_id == section_id)
        .filter(models.SectionTeacher.teacher_id == teacher_id)
        .first()
        is not None
    )
def count_section_attendance(db: Session, student_id: int, section_id: int | None = None) -> int:
    query = db.query(models.SectionAttendance).filter(models.SectionAttendance.student_id == student_id)
    if section_id is not None:
        query = query.filter(models.SectionAttendance.section_id == section_id)
    return query.count()
def add_section_beacon(db: Session, section_id: int, beacon_id: str) -> models.SectionBeacon:
    beacon = models.SectionBeacon(section_id=section_id, beacon_id=beacon_id)
    db.add(beacon)
    db.commit()
    db.refresh(beacon)
    return beacon
def list_section_beacons(db: Session, section_id: int) -> list[models.SectionBeacon]:
    return db.query(models.SectionBeacon).filter(models.SectionBeacon.section_id == section_id).all()
def is_beacon_allowed_for_section(db: Session, section_id: int, beacon_id: str) -> bool:
    return (
        db.query(models.SectionBeacon)
        .filter(models.SectionBeacon.section_id == section_id)
        .filter(models.SectionBeacon.beacon_id == beacon_id)
        .first()
        is not None
    )
