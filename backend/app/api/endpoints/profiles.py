from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.db.models import UserProfile, User

router = APIRouter()

class UserProfileBase(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    region: Optional[str] = None
    employment_status: Optional[str] = None
    interests: Optional[dict] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    
    class Config:
        orm_mode = True

@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    현재 사용자의 프로필 정보 조회
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="프로필이 없습니다")
    return profile

@router.post("/", response_model=UserProfileResponse)
def create_or_update_profile(
    *,
    db: Session = Depends(get_db),
    profile_in: UserProfileCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    사용자 프로필 생성 또는 업데이트
    - 프로필이 없는 경우: 새 프로필 생성
    - 프로필이 이미 있는 경우: 기존 프로필 업데이트
    """
    # 기존 프로필 확인
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile:
        # 기존 프로필 업데이트
        for key, value in profile_in.dict(exclude_unset=True).items():
            setattr(profile, key, value)
    else:
        # 새 프로필 생성
        profile = UserProfile(
            user_id=current_user.id,
            **profile_in.dict()
        )
        db.add(profile)
    
    db.commit()
    db.refresh(profile)
    return profile