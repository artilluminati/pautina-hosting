"""
Admin API Module

Маршруты (доступны только администраторам):

1. GET /admin/users
   - Описание: Получить список всех пользователей.
   - Headers:
     - Authorization: Bearer <access_token>
   - Response (200): list[UserRead]
     - Модель UserRead: id, name, email, phone, role, active, created_at
   - Ошибки:
     - 401 Unauthorized: при отсутствии или некорректном токене
     - 403 Forbidden: если роль текущего пользователя не admin

2. POST /admin/hosts/{host_id}/block
   - Описание: Заблокировать указанный хост.
   - Path Parameters:
     - host_id (int) - ID хоста для блокировки
   - Headers:
     - Authorization: Bearer <access_token>
   - Response (200): {"detail": "Host blocked"}
   - Ошибки:
     - 401 Unauthorized
     - 403 Forbidden
     - 404 Not Found: если хост с указанным ID не найден

3. POST /admin/hosts/{host_id}/archive
   - Описание: Архивировать указанный хост.
   - Path Parameters:
     - host_id (int) - ID хоста для архивации
   - Headers:
     - Authorization: Bearer <access_token>
   - Response (200): {"detail": "Host archived"}
   - Ошибки:
     - 401 Unauthorized
     - 403 Forbidden
     - 404 Not Found: если хост с указанным ID не найден
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, database, schemas
from .users import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"}
    }
)

@router.get(
    "/users",
    response_model=list[schemas.UserRead],
    status_code=status.HTTP_200_OK,
    summary="Список пользователей"
)
def list_users(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
) -> list[models.User]:
    """
    Получить список всех пользователей в базе данных.

    - Требует роль admin.
    - Возвращает список моделей UserRead.
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return db.query(models.User).all()

@router.post(
    "/hosts/{host_id}/block",
    status_code=status.HTTP_200_OK,
    summary="Блокировка хоста"
)
def block_host(
    host_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
) -> dict[str, str]:
    """
    Заблокировать указанный хост.

    Path Parameters:
    - host_id: ID хоста.

    Требует роль admin.

    Возвращает:
    - detail: Host blocked
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    host = db.get(models.Host, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    host.status = models.StatusEnum.disabled
    db.commit()
    return {"detail": "Host blocked"}

@router.post(
    "/hosts/{host_id}/archive",
    status_code=status.HTTP_200_OK,
    summary="Архивация хоста"
)
def archive_host(
    host_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
) -> dict[str, str]:
    """
    Архивировать указанный хост.

    Path Parameters:
    - host_id: ID хоста.

    Требует роль admin.

    Возвращает:
    - detail: Host archived
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    host = db.get(models.Host, host_id)
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    host.status = models.StatusEnum.archived
    db.commit()
    return {"detail": "Host archived"}