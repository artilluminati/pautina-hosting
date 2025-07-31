# backend/src/app/routers/hosts.py

"""
Hosts API Module

Маршруты для управления хостами текущего пользователя.

1. POST /hosts/
   - Описание: Создать новый хост.
   - Headers:
     - Authorization: Bearer <access_token>
   - Body (JSON):
     - subdomain (str) — желаемый поддомен.
     - plan (PlanEnum) — тарифный план («demo» или «yearly»).
   - Response (200): HostRead
     - id, subdomain, plan, status, expires_at
   - Ошибки:
     - 401 Unauthorized — если токен отсутствует или недействителен.
     - 400 Bad Request — если переданы невалидные данные (например, дублирующийся subdomain).

2. GET /hosts/
   - Описание: Получить список всех хостов, принадлежащих текущему пользователю.
   - Headers:
     - Authorization: Bearer <access_token>
   - Response (200): list[HostRead]
   - Ошибки:
     - 401 Unauthorized

3. GET /hosts/{host_id}
   - Описание: Получить подробную информацию по конкретному хосту.
   - Headers:
     - Authorization: Bearer <access_token>
   - Path Parameters:
     - host_id (int) — ID запрашиваемого хоста.
   - Response (200): HostDetail
     - все поля HostRead + FTP/SSH/MySQL/Mail учетные данные
   - Ошибки:
     - 401 Unauthorized
     - 404 Not Found — если хост не найден или не принадлежит текущему пользователю.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, models, database
from .users import get_current_user

router = APIRouter(
    prefix="/hosts",
    tags=["Hosts"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not Found"},
        400: {"description": "Bad Request"},
    }
)

@router.post(
    "/",
    response_model=schemas.HostRead,
    status_code=status.HTTP_200_OK,
    summary="Создать новый хост"
)
def create_host(
    host_in: schemas.HostCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
) -> models.Host:
    """
    Создать новый хост для текущего пользователя.

    Body:
    - subdomain: str
    - plan: PlanEnum

    Возвращает:
    - HostRead

    Ошибки:
    - 401 Unauthorized
    - 400 Bad Request
    """
    host = models.Host(
        subdomain=host_in.subdomain,
        plan=host_in.plan,
        owner_id=current_user.id
    )
    db.add(host)
    db.commit()
    db.refresh(host)
    return host

@router.get(
    "/",
    response_model=list[schemas.HostRead],
    status_code=status.HTTP_200_OK,
    summary="Список хостов пользователя"
)
def list_hosts(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
) -> list[models.Host]:
    """
    Получить все хосты, принадлежащие текущему пользователю.

    Возвращает:
    - list[HostRead]

    Ошибки:
    - 401 Unauthorized
    """
    return db.query(models.Host).filter(models.Host.owner_id == current_user.id).all()

@router.get(
    "/{host_id}",
    response_model=schemas.HostDetail,
    status_code=status.HTTP_200_OK,
    summary="Детали хоста"
)
def get_host(
    host_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
) -> models.Host:
    """
    Получить подробную информацию о хосте по его ID.

    Path Parameters:
    - host_id: int

    Возвращает:
    - HostDetail

    Ошибки:
    - 401 Unauthorized
    - 404 Not Found
    """
    host = db.get(models.Host, host_id)
    if not host or host.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    return host
