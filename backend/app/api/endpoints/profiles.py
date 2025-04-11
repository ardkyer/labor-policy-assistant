from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.db.models import User, UserProfile, Policy, Notification

router = APIRouter()

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    employment_status: Optional[str] = None
    region: Optional[str] = None
    # 새로운 필드 추가
    is_disabled: Optional[bool] = None
    is_foreign: Optional[bool] = None
    family_status: Optional[str] = None
    interests: Optional[Dict] = None

@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    현재 사용자의 프로필 정보 조회
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # 연령대 변환
    age_group = ""
    if profile and profile.age:
        if profile.age < 35:
            age_group = "youth"
        elif profile.age < 65:
            age_group = "middle"
        else:
            age_group = "senior"
    
    # 프로필이 없으면 빈 프로필 반환
    if not profile:
        return {
            "email": current_user.email,
            "name": current_user.full_name,
            "profile": {}
        }
    
    return {
        "email": current_user.email,
        "name": current_user.full_name,
        "profile": {
            "age": age_group,
            "gender": profile.gender,
            "employment_status": profile.employment_status,
            "region": profile.region,
            "interests": profile.interests or {}
        }
    }

@router.put("/me")
def update_profile(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile_data: ProfileUpdate,
) -> Any:
    """
    사용자 프로필 정보 업데이트
    """
    # 사용자 이름 업데이트
    if profile_data.name is not None:
        current_user.full_name = profile_data.name
        db.add(current_user)
    
    # 프로필 정보 업데이트
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # 연령대를 나이로 변환
    age_value = None
    if profile_data.age:
        if profile_data.age == "youth":
            age_value = 25
        elif profile_data.age == "middle":
            age_value = 45
        elif profile_data.age == "senior":
            age_value = 70
    
    # 프로필이 없으면 새로 생성
    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            age=age_value,
            gender=profile_data.gender,
            employment_status=profile_data.employment_status,
            region=profile_data.region,
            # 새 필드 추가
            is_disabled=profile_data.is_disabled,
            is_foreign=profile_data.is_foreign,
            family_status=profile_data.family_status,
            interests=profile_data.interests or {}
        )
        db.add(profile)
    else:
        # 존재하는 프로필 업데이트
        if profile_data.age is not None:
            profile.age = age_value
        if profile_data.gender is not None:
            profile.gender = profile_data.gender
        if profile_data.employment_status is not None:
            profile.employment_status = profile_data.employment_status
        if profile_data.region is not None:
            profile.region = profile_data.region
        # 새 필드 업데이트
        if profile_data.is_disabled is not None:
            profile.is_disabled = profile_data.is_disabled
        if profile_data.is_foreign is not None:
            profile.is_foreign = profile_data.is_foreign
        if profile_data.family_status is not None:
            profile.family_status = profile_data.family_status
        if profile_data.interests is not None:
            profile.interests = profile_data.interests
        db.add(profile)
    
    db.commit()
    db.refresh(profile)
    
    return {
        "message": "프로필 정보가 성공적으로 업데이트되었습니다."
    }

@router.get("/me/saved-policies")
def get_saved_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List:
    """
    사용자가 저장한 정책 목록 조회 (이 부분은 관심 정책을 저장하는 테이블 구조에 따라 달라질 수 있음)
    """
    # 이 부분은 UserProfile의 interests 필드나 별도 테이블에서 가져와야 함
    # 지금은 빈 배열 반환
    return []

@router.get("/me/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List:
    """
    사용자 알림 목록 조회
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    result = []
    for notification in notifications:
        result.append({
            "id": notification.id,
            "title": notification.title,
            "message": notification.content,
            "type": notification.type,
            "is_read": notification.is_read,
            "createdAt": notification.created_at.isoformat()
        })
    
    return result