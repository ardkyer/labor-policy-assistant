from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.api.deps import get_db, get_current_user
from app.db.models import User, UserProfile

router = APIRouter()

# 프로필 정보를 위한 스키마
class ProfileCreate(BaseModel):
    age: Optional[str] = None
    gender: Optional[str] = None
    employment_status: Optional[str] = None
    region: Optional[str] = None
    is_disabled: Optional[str] = None  # 추가
    is_foreign: Optional[str] = None   # 추가
    family_status: Optional[str] = None  # 추가

# 회원가입 요청 모델
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    profile: Optional[ProfileCreate] = None

@router.post("/login")
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 호환 토큰 로그인
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="비활성 사용자")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=dict)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_data: UserRegister,
):
    """
    새 사용자 등록 및 프로필 정보 저장
    """
    # 이미 등록된 이메일 확인
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="이미 등록된 이메일입니다.",
        )
    
    # 새 사용자 생성
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 프로필 정보가 제공된 경우 저장
    if user_data.profile:
        # age 필드는 문자열에서 정수로 변환
        age_value = None
        if user_data.profile.age:
            # 연령대 문자열에 따라 대표 나이 값 설정
            if user_data.profile.age == "youth":
                age_value = 25  # 청년 대표 나이
            elif user_data.profile.age == "middle":
                age_value = 45  # 중장년 대표 나이
            elif user_data.profile.age == "senior":
                age_value = 70  # 노년 대표 나이
        
        # 새 필드 처리 - 문자열 "true"/"false"를 불리언으로 변환
        is_disabled = user_data.profile.is_disabled == "true"
        is_foreign = user_data.profile.is_foreign == "true"
        
        profile = UserProfile(
            user_id=new_user.id,
            age=age_value,
            gender=user_data.profile.gender,
            employment_status=user_data.profile.employment_status,
            region=user_data.profile.region,
            is_disabled=is_disabled,  # 추가
            is_foreign=is_foreign,    # 추가
            family_status=user_data.profile.family_status,  # 추가
            interests={}  # 기본 빈 JSON 객체
        )
        db.add(profile)
        db.commit()
    
    return {"message": "사용자가 성공적으로 등록되었습니다", "user_id": new_user.id}

@router.get("/me", response_model=dict)
def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    현재 사용자 정보 가져오기 (프로필 정보 포함)
    """
    # 사용자 프로필 정보 가져오기
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # 프로필이 없으면 기본 정보만 반환
    if not profile:
        return {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
        }
    
    # 연령대 변환
    age_group = ""
    if profile.age:
        if profile.age < 35:
            age_group = "youth"
        elif profile.age < 65:
            age_group = "middle"
        else:
            age_group = "senior"
    
    # 프로필 정보 포함하여 반환
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "profile": {
            "age": age_group,
            "gender": profile.gender,
            "employment_status": profile.employment_status,
            "region": profile.region,
            "is_disabled": profile.is_disabled,  # 추가
            "is_foreign": profile.is_foreign,    # 추가
            "family_status": profile.family_status,  # 추가
            "interests": profile.interests or {}
        }
    }