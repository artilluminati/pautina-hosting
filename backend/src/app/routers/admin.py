from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, database
from .users import get_current_user
from .. import schemas

router = APIRouter()

@router.get("/users", response_model=list[schemas.UserRead])
def list_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Получить список всех пользователей в базе данных.

    Доступно только для администраторов.

    Возвращает:
        List[UserRead]: Список всех пользователей в базе данных.
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403)
    return db.query(models.User).all()

@router.post("/hosts/{host_id}/block")
def block_host(host_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Заблокировать хост.

    Доступно только для администраторов.

    Args:
        host_id: ID хоста, который нужно заблокировать.

    Returns:
        Dict[str, str]: {"detail": "Host blocked"}
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403)
    host = db.get(models.Host, host_id)
    if not host:
        raise HTTPException(status_code=404)
    host.status = models.StatusEnum.disabled
    db.commit()
    return {"detail": "Host blocked"}

@router.post("/hosts/{host_id}/archive")
def archive_host(host_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """Архивировать хост.

    Доступно только для администраторов.

    Args:
        host_id: ID хоста, который нужно архивировать.

    Returns:
        Dict[str, str]: {"detail": "Host archived"}
    """
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403)
    host = db.get(models.Host, host_id)
    if not host:
        raise HTTPException(status_code=404)
    host.status = models.StatusEnum.archived
    db.commit()
    return {"detail": "Host archived"}