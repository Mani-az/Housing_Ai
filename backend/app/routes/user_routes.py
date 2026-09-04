from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user, get_users, get_user_by_id, delete_member


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/", response_model=UserResponse)
def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    return create_user(db=db, user_data=user_data)


@router.get("/", response_model=list[UserResponse])
def read_users(
    db: Session = Depends(get_db),
):
    return get_users(db=db)


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    return get_user_by_id(db=db, user_id=user_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member_account(
    user_id: int,
    db: Session = Depends(get_db),
):
    delete_member(db=db, user_id=user_id)
    return None
