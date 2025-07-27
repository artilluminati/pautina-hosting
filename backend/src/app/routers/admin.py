from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, database
from .users import get_current_user
from .. import schemas

router = APIRouter()

@router.get("/users", response_model=list[schemas.UserRead])
def list_users(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403)
    return db.query(models.User).all()

@router.post("/hosts/{host_id}/block")
def block_host(host_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403)
    host = db.query(models.Host).get(host_id)
    if not host:
        raise HTTPException(status_code=404)
    host.status = models.StatusEnum.disabled
    db.commit()
    return {"detail": "Host blocked"}

@router.post("/hosts/{host_id}/archive")
def archive_host(host_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403)
    host = db.query(models.Host).get(host_id)
    if not host:
        raise HTTPException(status_code=404)
    host.status = models.StatusEnum.archived
    db.commit()
    return {"detail": "Host archived"}