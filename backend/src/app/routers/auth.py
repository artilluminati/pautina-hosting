from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas, models, database
from ..core.security import verify_password, get_password_hash, create_access_token

router = APIRouter()

def get_user_by_email(db, email):
    """
    Получение пользователя из базы данных по его электронной почте.

    Args:
        db (Session): Сессия базы данных.
        email (str): Электронная почта пользователя, которого нужно получить.

    Returns:
        User: Объект пользователя, если он найден, иначе None.
    """

    return db.query(models.User).filter(models.User.email == email).first()

@router.post("/register", response_model=schemas.UserRead)
def register(user_in: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    Регистрация пользователя.

    Args:
        user_in (schemas.UserCreate): Данные регистрируемого пользователя.

    Returns:
        schemas.UserRead: Объект регистрируемого пользователя.

    Exceptions:
        HTTPException: 400, если пользователь с email уже зарегистрирован.
    """
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    """
    Авторизация пользователя.

    Args:
        form_data (OAuth2PasswordRequestForm): Форма авторизации.
        db (Session): Сессия базы данных.

    Returns:
        schemas.Token: Объект токена.

    Exceptions:
        HTTPException: 401, если данные для авторизации неверны.
    """
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}