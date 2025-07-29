from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError
from ..schemas import TokenData
import os

# Инициализация Argon2 PasswordHasher
ph = PasswordHasher()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли простой пароль хешу Argon2."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def get_password_hash(password: str) -> str:
    """Генерирует хеш пароля с использованием Argon2."""
    return ph.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Создает JWT с полезной нагрузкой и временем жизни."""
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> TokenData | None:
    """Декодирует JWT и возвращает данные пользователя или None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(user_id=payload.get("sub"), role=payload.get("role"))
    except PyJWTError:
        return None