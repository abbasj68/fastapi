from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.cafe_services import get_nearest_cafes

router = APIRouter(prefix="/cafes", tags=["cafes"])

@router.get("/nearest")
def nearest_cafes(lat : float, lon: float, db: Session=Depends(get_db)):
    return get_nearest_cafes(db, user_lat=lat, user_lon=lon)
    