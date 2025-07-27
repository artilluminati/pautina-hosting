from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .models import User, RoleEnum
from .core.security import get_password_hash
from .routers import auth, users, hosts, admin
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os

# Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["http://localhost:5173", "localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# стартап‑хэндлер для сидирования админа и тестового юзера
@asynccontextmanager
async def lifespan(app: FastAPI):
    db: Session = SessionLocal()
    try:
        # админ
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        if not db.query(User).filter(User.email == admin_email).first():
            db.add(
                User(
                    name="Administrator",
                    email=admin_email,
                    hashed_password=get_password_hash(admin_pass),
                    role=RoleEnum.admin,
                )
            )
        # простой пользователь
        user_email = os.getenv("TEST_EMAIL", "user@example.com")
        user_pass = os.getenv("TEST_PASSWORD", "user123")
        if not db.query(User).filter(User.email == user_email).first():
            db.add(
                User(
                    name="Test User",
                    email=user_email,
                    hashed_password=get_password_hash(user_pass),
                    role=RoleEnum.user,
                )
            )
        db.commit()
    finally:
        db.close()
    yield

# подключаем роуты
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(hosts.router, prefix="/hosts", tags=["Hosts"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Hello World"}