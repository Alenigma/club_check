
from pydantic import BaseModel
from typing import Optional
import datetime

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AttendanceBase(BaseModel):
    student_id: int

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

class ManualAttendance(BaseModel):
    student_id: int
    section_id: int

class SectionBase(BaseModel):
    name: str
class SectionCreate(SectionBase):
    pass
class Section(SectionBase):
    id: int

    class Config:
        from_attributes = True
class SectionMembership(BaseModel):
    section_id: int
    user_id: int
class SectionAttendanceBase(BaseModel):
    section_id: int
    student_id: int
class SectionAttendanceCreate(SectionAttendanceBase):
    pass
class SectionAttendance(SectionAttendanceBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        from_attributes = True
class SectionBeaconBase(BaseModel):
    section_id: int
    beacon_id: str
class SectionBeaconCreate(SectionBeaconBase):
    pass
class SectionBeacon(SectionBeaconBase):
    id: int

    class Config:
        from_attributes = True
