"""
Auth API Module

Маршруты:

1. POST /auth/register
   - Описание: Регистрация нового пользователя.
   - Body (JSON):
     - name (str) - имя пользователя.
     - email (EmailStr) - email.
     - password (Optional[str]) - временный пароль (используется игнорируется).
     - phone (str) - номер телефона.
     - agree_terms (bool) - согласие с пользовательским соглашением.
     - agree_privacy (bool) - согласие с политикой приватности.
   - Response (200): schemas.UserReadAfterRegister:
     - id, name, email, phone, role, active, created_at, token
   - Ответ ошибки:
     - 400 Bad Request: "Вы не согласились...", "Адрес электронной почты...", "Номер телефона уже зарегистрирован"

2. POST /auth/login
   - Описание: Авторизация пользователя.
   - Body (form data):
     - username (str) - email пользователя.
     - password (str) - пароль пользователя.
   - Response (200): schemas.Token:
     - access_token (str), token_type (str="bearer").
   - Ошибки:
     - 401 Unauthorized: "Invalid credentials"

3. POST /auth/recover
   - Описание: Восстановление пароля по телефону.
   - Body (JSON):
     - phone (str) - номер телефона.
   - Response (200): schemas.PasswordRecoverResponse:
     - login (EmailStr), password (str) - новый временный пароль.
   - Ошибки:
     - 404 Not Found: "User with this phone not found"
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from uuid import uuid4
import string
from random import SystemRandom

from .. import schemas, models, database
from ..core.security import verify_password, get_password_hash, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not Found"},
        400: {"description": "Bad Request"}
    }
)

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """
    Получение пользователя по email.

    Args:
        db: Session - сессия БД.
        email: str - email.
    Returns:
        User или None.
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_phone(db: Session, phone: str) -> models.User | None:
    """
    Получение пользователя по номеру телефона.

    Args:
        db: Session - сессия БД.
        phone: str - номер телефона.
    Returns:
        User или None.
    """
    return db.query(models.User).filter(models.User.phone == phone).first()


def generate_random_password(length: int = 10) -> str:
    """
    Генерация случайного временного пароля.

    Args:
        length: int - длина пароля.
    Returns:
        str - сгенерированный пароль.
    """
    chars = string.ascii_letters + string.digits
    return ''.join(SystemRandom().choice(chars) for _ in range(length))


def is_invalid_agreements(user_in: schemas.UserRegister) -> bool:
    """
    Проверяет, даны ли оба необходимых согласия.

    Args:
        user_in: UserRegister
    Returns:
        True, если отсутствует хотя бы одно согласие.
    """
    return not (user_in.agree_terms and user_in.agree_privacy)

@router.post(
    "/register",
    response_model=schemas.UserReadAfterRegister,
    status_code=status.HTTP_200_OK,
    summary="Регистрация пользователя"
)
def register(
    user_in: schemas.UserRegister,
    db: Session = Depends(database.get_db)
) -> schemas.UserReadAfterRegister:
    """
    Регистрация пользователя.

    - Проверка согласий и уникальности email/phone.
    - Генерация временного пароля и одноразового токена.
    - Сохранение пароля (хэш) и пользователя в БД, временную пару в TempPassword.

    Args:
        user_in: UserRegister - данные регистрации.
        db: Session - сессия БД.

    Returns:
        UserReadAfterRegister с полем token для бота.
    """
    if is_invalid_agreements(user_in):
        raise HTTPException(status_code=400, detail="Вы не согласились с условиями использования сервиса")
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Адрес электронной почты уже зарегистрирован")
    if get_user_by_phone(db, user_in.phone):
        raise HTTPException(status_code=400, detail="Номер телефона уже зарегистрирован")

    temp_password = generate_random_password()
    token = uuid4().hex

    # Сохраняем временный пароль для выдачи через бота
    db.add(models.TempPassword(token=token, temp_password=temp_password))

    # Создаём пользователя
    user = models.User(
        name=user_in.name,
        email=user_in.email,
        phone=user_in.phone,
        hashed_password=get_password_hash(temp_password),
        phone_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        **user.__dict__,
        "token": token
    }

@router.post(
    "/login",
    response_model=schemas.Token,
    status_code=status.HTTP_200_OK,
    summary="Логин пользователя"
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
) -> schemas.Token:
    """
    Авторизация пользователя.

    Body form-data:
    - username: email
    - password: пароль

    Returns:
    - access_token, token_type

    Ошибки:
    - 401: Invalid credentials
    """
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}

@router.post(
    "/recover",
    response_model=schemas.PasswordRecoverResponse,
    status_code=status.HTTP_200_OK,
    summary="Восстановление пароля"
)
def recover_password(
    req: schemas.PasswordRecoverRequest,
    db: Session = Depends(database.get_db)
) -> schemas.PasswordRecoverResponse:
    """
    Восстановление пароля по номеру телефона.

    Body JSON:
    - phone: str

    Returns:
    - login (email), password (новый временный пароль)

    Ошибки:
    - 404: User with this phone not found
    """
    user = get_user_by_phone(db, req.phone)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User with this phone not found")
    new_password = generate_random_password()
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    return schemas.PasswordRecoverResponse(login=user.email, password=new_password)
