from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine, SessionLocal
from .api import api_router
from . import crud, schemas
from .config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    if settings.create_tables_on_startup:
        models.Base.metadata.create_all(bind=engine)
    if settings.seed_on_startup:
        seed_initial_data()


def seed_initial_data():
    db = SessionLocal()
    try:
        teacher = crud.get_user_by_username(db, username="teacher")
        if not teacher:
            teacher = crud.create_user(
                db,
                schemas.UserCreate(
                    username="teacher", full_name="Prof. Teacher", password="teacherpass", role="teacher"
                ),
            )
        student = crud.get_user_by_username(db, username="student")
        if not student:
            student = crud.create_user(
                db,
                schemas.UserCreate(
                    username="student", full_name="John Student", password="studentpass", role="student"
                ),
            )

        sections = crud.list_sections(db)
        default_section = next((s for s in sections if s.name == "Default Section"), None)
        if not default_section:
            default_section = crud.create_section(db, schemas.SectionCreate(name="Default Section"))

        if teacher and not crud.is_teacher_in_section(db, default_section.id, teacher.id):
            crud.add_teacher_to_section(db, default_section.id, teacher.id)
        if student and not crud.is_student_in_section(db, default_section.id, student.id):
            crud.add_student_to_section(db, default_section.id, student.id)
    finally:
        db.close()


app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Welcome to Club Check API"}