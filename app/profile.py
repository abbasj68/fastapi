from fastapi import APIRouter, Depends , HTTPException, status
from sqlalchemy.orm import Session
from . import models , database, utils
from .schemas import ProfileUpdate ,ChangePassword
from .auth import get_current_user

router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)

@router.get("/")
def get_profile(current_user: models.User= Depends(get_current_user)):
    return{
        "id":current_user.id,
        "username":current_user.username,
        "email":current_user.email,
        "name":current_user.name,
        "location":current_user.location,
        "is_superuser":current_user.is_superuser,
    }
    
@router.put("/")
def update_profile(
    profile_data: ProfileUpdate,
    db: Session =Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")
    if profile_data.name:
        user.name = profile_data.name
    if profile_data.email:
        user.email = profile_data.email
    if profile_data.location:
        user.location = profile_data.location
        
    db.commit()
    db.refresh(user)
    return {"message":"Profile updated successfully"}

@router.put("/password")
def change_password(
    password_date: ChangePassword,
    db: Session=Depends(database.get_db),
    current_user: models.User =Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")
    
    if not utils.verify_password(password_date.old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="Old password is incorrect")
    
    user.hashed_password = utils.hash_password(password_date.new_password)
    db.commit()
    return {"message":"Password updated successfully"}

@router.delete("/")
def delete_account(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message":"Acount deleted successfully"}