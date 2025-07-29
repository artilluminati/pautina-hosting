from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .models import User, RoleEnum
from .core.security import get_password_hash
from .routers import auth, users, hosts, admin
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import os

# Контекст управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создание таблиц при старте
    Base.metadata.create_all(bind=engine)
    print("Database connected and tables created!")

    # Сидирование админа и тестового пользователя
    db = SessionLocal()
    try:
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

        test_email = os.getenv("TEST_EMAIL", "user@example.com")
        test_pass = os.getenv("TEST_PASSWORD", "user123")
        if not db.query(User).filter(User.email == test_email).first():
            db.add(
                User(
                    name="Test User",
                    email=test_email,
                    hashed_password=get_password_hash(test_pass),
                    role=RoleEnum.user,
                )
            )

        db.commit()
    finally:
        db.close()

    yield

    # Здесь можно добавить логику при завершении (shutdown), если нужно

# Инициализация приложения с lifespan
app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:5173", "localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# подключаем роуты
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(hosts.router, prefix="/hosts", tags=["Hosts"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Hello World"}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}