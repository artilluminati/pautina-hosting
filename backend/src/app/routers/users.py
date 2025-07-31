# backend/src/app/routers/users.py

"""
Users API Module

Модуль для получения информации о текущем пользователе на основе JWT-токена.

1. GET /users/me
   - Описание: Получить информацию о текущем пользователе.
   - Headers:
     - Authorization: Bearer <access_token>
   - Response (200): UserRead
     - id, name, email, phone, role, active, created_at
   - Ошибки:
     - 401 Unauthorized — если токен отсутствует или недействителен.
     - 404 Not Found — если пользователь из токена не найден в БД.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from .. import schemas, models, database
from ..core.security import decode_access_token

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not Found"}
    }
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
) -> models.User:
    """
    Депенденси для извлечения текущего пользователя из JWT-токена.

    Args:
    - token: str (Bearer <token>)
    - db: Session

    Returns:
    - models.User

    Ошибки:
    - HTTP 401: Invalid token
    - HTTP 404: User not found
    """
    token_data = decode_access_token(token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(models.User, token_data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get(
    "/me",
    response_model=schemas.UserRead,
    status_code=status.HTTP_200_OK,
    summary="Информация о текущем пользователе"
)
def read_users_me(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Возвращает данные текущего аутентифицированного пользователя.

    Ошибки:
    - 401 Unauthorized
    - 404 Not Found
    """
    return current_user
