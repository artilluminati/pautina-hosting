from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, database
from .users import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.HostRead)
def create_host(host_in: schemas.HostCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    host = models.Host(
        subdomain=host_in.subdomain,
        plan=host_in.plan,
        owner_id=current_user.id
    )
    db.add(host)
    db.commit()
    db.refresh(host)
    return host

@router.get("/", response_model=list[schemas.HostRead])
def list_hosts(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Host).filter(models.Host.owner_id == current_user.id).all()

@router.get("/{host_id}", response_model=schemas.HostDetail)
def get_host(host_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    host = db.query(models.Host).get(host_id)
    if not host or host.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Host not found")
    return host