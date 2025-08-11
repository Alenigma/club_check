
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default="student")
    otp_secret = Column(String, nullable=True)
    master_qr_mode_enabled = Column(Boolean, default=False)
    master_qr_secret = Column(String, nullable=True)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("User")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class SectionBeacon(Base):
    __tablename__ = "section_beacons"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), index=True)
    beacon_id = Column(String, index=True)


class SectionStudent(Base):
    __tablename__ = "section_students"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)


class SectionTeacher(Base):
    __tablename__ = "section_teachers"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), index=True)


class SectionAttendance(Base):
    __tablename__ = "section_attendance"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), index=True)
    student_id = Column(Integer, ForeignKey("users.id"), index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
