from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine, SessionLocal
from .api import api_router
from . import crud, schemas

models.Base.metadata.create_all(bind=engine)

# Create initial data
def create_initial_data():
    db = SessionLocal()
    # Create teacher
    teacher = crud.get_user_by_username(db, username="teacher")
    if not teacher:
        crud.create_user(db, user=schemas.UserCreate(username="teacher", full_name="Prof. Teacher", password="teacherpass", role="teacher"))
    # Create student
    student = crud.get_user_by_username(db, username="student")
    if not student:
        crud.create_user(db, user=schemas.UserCreate(username="student", full_name="John Student", password="studentpass", role="student"))
    db.close()

create_initial_data()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to Club Check API"}