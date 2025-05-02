from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.api.deps import get_db, get_current_user
from app.db.models import User, UserProfile, ProfileType, ProfileRecommendation
from app.services.policy_matcher import PolicyMatcher

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

# 프로필 업데이트 모델
class ProfileUpdate(BaseModel):
    age: Optional[str] = None
    gender: Optional[str] = None
    employment_status: Optional[str] = None
    region: Optional[str] = None
    is_disabled: Optional[str] = None
    is_foreign: Optional[str] = None
    family_status: Optional[str] = None

def get_or_create_profile_type(db: Session, profile_data: dict) -> int:
    """프로필 데이터에 맞는 ProfileType을 찾거나 생성하고 ID를 반환"""
    
    # 연령대 변환
    age_group = "청년"  # 기본값
    if profile_data.get("age"):
        if profile_data["age"] == "youth":
            age_group = "청년"
        elif profile_data["age"] == "middle":
            age_group = "중장년"
        elif profile_data["age"] == "senior":
            age_group = "노년"
    
    # 성별 변환
    gender = "기타"  # 기본값
    if profile_data.get("gender"):
        if profile_data["gender"] == "male":
            gender = "남성"
        elif profile_data["gender"] == "female":
            gender = "여성"
        elif profile_data["gender"] == "other":
            gender = "기타"
    
    # 고용상태 변환
    employment_status = "구직자"  # 기본값
    if profile_data.get("employment_status"):
        if profile_data["employment_status"] == "employed":
            employment_status = "재직자"
        elif profile_data["employment_status"] == "unemployed":
            employment_status = "구직자"
        elif profile_data["employment_status"] == "business":
            employment_status = "자영업자"
        elif profile_data["employment_status"] == "student":
            employment_status = "학생"
    
    # 장애인 여부 (문자열 "true"/"false"를 불리언으로 변환)
    is_disabled = profile_data.get("is_disabled") == "true"
    
    # 외국인 여부 (문자열 "true"/"false"를 불리언으로 변환)
    is_foreign = profile_data.get("is_foreign") == "true"
    
    # 가족 상황 변환
    family_status = "해당 없음"  # 기본값
    if profile_data.get("family_status"):
        if profile_data["family_status"] == "parent":
            family_status = "영유아 자녀 있음"
        elif profile_data["family_status"] == "single_parent":
            family_status = "한부모"
        elif profile_data["family_status"] == "caregiver":
            family_status = "주 양육자"
        elif profile_data["family_status"] == "none":
            family_status = "해당 없음"
    
    # 이미 존재하는 프로필 유형인지 확인
    profile_type = db.query(ProfileType).filter(
        ProfileType.age_group == age_group,
        ProfileType.gender == gender,
        ProfileType.employment_status == employment_status,
        ProfileType.is_disabled == is_disabled,
        ProfileType.is_foreign == is_foreign,
        ProfileType.family_status == family_status
    ).first()
    
    # 존재하지 않으면 새로 생성
    if not profile_type:
        profile_type = ProfileType(
            age_group=age_group,
            gender=gender,
            employment_status=employment_status,
            is_disabled=is_disabled,
            is_foreign=is_foreign,
            family_status=family_status
        )
        db.add(profile_type)
        db.commit()
        db.refresh(profile_type)
    
    return profile_type.id

def extract_title_from_text(text: str) -> str:
    """텍스트에서 제목 추출 (첫번째 유의미한 줄 사용)"""
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line and len(line) < 100:  # 적당한 길이의 줄 찾기
            return line
    return "제목 없음"

def extract_category(text: str) -> str:
    """텍스트 내용 기반으로 카테고리 추정"""
    categories = {
        "청년": ["청년", "20대", "30대", "학졸자", "구직자"],
        "고령자": ["고령자", "신중년", "50대", "60대"],
        "장애인": ["장애인", "중증장애", "경증장애"],
        "여성": ["여성", "육아", "출산", "모성"],
        "외국인": ["외국인", "다문화", "이주민"],
        "사업주": ["사업주", "기업", "고용주", "사업장"],
        "직업능력개발": ["직업훈련", "능력개발", "자격증", "교육훈련"]
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category
    
    return "기타"

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
    
    profile_type_id = None
    
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
        
        # 프로필 유형 ID 가져오기
        profile_type_id = get_or_create_profile_type(db, user_data.profile.dict())
        
        profile = UserProfile(
            user_id=new_user.id,
            age=age_value,
            gender=user_data.profile.gender,
            employment_status=user_data.profile.employment_status,
            region=user_data.profile.region,
            is_disabled=is_disabled,  # 추가
            is_foreign=is_foreign,    # 추가
            family_status=user_data.profile.family_status,  # 추가
            interests={},  # 기본 빈 JSON 객체
            profile_type_id=profile_type_id  # 프로필 유형 ID 추가
        )
        db.add(profile)
        db.commit()
    
    # 프로필 유형 ID가 있는 경우, 해당 유형에 맞는 추천 정책 생성
    if profile_type_id:
        # 기존 추천 정책이 있는지 확인
        existing_recommendations = db.query(ProfileRecommendation).filter(
            ProfileRecommendation.profile_type_id == profile_type_id
        ).all()
        
        # 기존 추천 정책이 없으면 생성
        if not existing_recommendations:
            try:
                # 여기서 scripts.generate_profile_recommendations의 로직을 가져와서 사용
                from app.services.policy_matcher import PolicyMatcher
                
                # 프로필 타입 정보 가져오기
                profile_type = db.query(ProfileType).filter(ProfileType.id == profile_type_id).first()
                
                if profile_type:
                    # 정책 매처 초기화
                    policy_matcher = PolicyMatcher()
                    
                    # 프로필 딕셔너리 생성
                    profile_dict = {
                        "age": 25 if profile_type.age_group == "청년" else 45 if profile_type.age_group == "중장년" else 65,
                        "gender": "male" if profile_type.gender == "남성" else "female" if profile_type.gender == "여성" else "other",
                        "employment_status": (
                            "employed" if profile_type.employment_status == "재직자" else
                            "unemployed" if profile_type.employment_status == "구직자" else
                            "business" if profile_type.employment_status == "자영업자" else "student"
                        ),
                        "is_disabled": profile_type.is_disabled,
                        "is_foreign": profile_type.is_foreign,
                        "family_status": (
                            "parent" if profile_type.family_status == "영유아 자녀 있음" else
                            "single_parent" if profile_type.family_status == "한부모" else
                            "caregiver" if profile_type.family_status == "주 양육자" else "none"
                        )
                    }
                    
                    # 정책 추천 가져오기
                    recommendations = policy_matcher.recommend_policies(profile_dict, top_k=5)
                    
                    # 추천 저장
                    for rank, rec in enumerate(recommendations, 1):
                        policy_text = rec.get("text", "")
                        policy_title = rec.get("title") or extract_title_from_text(policy_text)
                        
                        recommendation = ProfileRecommendation(
                            profile_type_id=profile_type.id,
                            policy_id=rec.get("id", "") or rec.get("policy_id", ""),
                            policy_title=policy_title,
                            policy_content=policy_text,
                            page_number=rec.get("page", ""),
                            category=rec.get("category") or extract_category(policy_text),
                            relevance_score=rec.get("score", 0.0),
                            rank_order=rank
                        )
                        db.add(recommendation)
                    
                    db.commit()
            except Exception as e:
                print(f"추천 정책 생성 중 오류 발생: {str(e)}")
                # 오류가 발생해도 회원가입은 성공하도록 오류를 무시
    
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
    
    # 프로필이 없으면 기본 정보만 반환//
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

@router.put("/me/profile", response_model=dict)
def update_user_profile(
    *,
    db: Session = Depends(get_db),
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 프로필 정보 업데이트
    """
    # 사용자 프로필 가져오기
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    # 프로필이 없으면 새로 생성
    if not profile:
        # age 필드는 문자열에서 정수로 변환
        age_value = None
        if profile_data.age:
            if profile_data.age == "youth":
                age_value = 25  # 청년 대표 나이
            elif profile_data.age == "middle":
                age_value = 45  # 중장년 대표 나이
            elif profile_data.age == "senior":
                age_value = 70  # 노년 대표 나이
        
        # 새 필드 처리 - 문자열 "true"/"false"를 불리언으로 변환
        is_disabled = profile_data.is_disabled == "true"
        is_foreign = profile_data.is_foreign == "true"
        
        # 프로필 유형 ID 가져오기
        profile_type_id = get_or_create_profile_type(db, profile_data.dict())
        
        profile = UserProfile(
            user_id=current_user.id,
            age=age_value,
            gender=profile_data.gender,
            employment_status=profile_data.employment_status,
            region=profile_data.region,
            is_disabled=is_disabled,
            is_foreign=is_foreign,
            family_status=profile_data.family_status,
            interests={},
            profile_type_id=profile_type_id
        )
        db.add(profile)
    else:
        # 기존 프로필 업데이트
        if profile_data.age:
            age_value = None
            if profile_data.age == "youth":
                age_value = 25
            elif profile_data.age == "middle":
                age_value = 45
            elif profile_data.age == "senior":
                age_value = 70
            profile.age = age_value
        
        if profile_data.gender is not None:
            profile.gender = profile_data.gender
            
        if profile_data.employment_status is not None:
            profile.employment_status = profile_data.employment_status
            
        if profile_data.region is not None:
            profile.region = profile_data.region
            
        if profile_data.is_disabled is not None:
            profile.is_disabled = profile_data.is_disabled == "true"
            
        if profile_data.is_foreign is not None:
            profile.is_foreign = profile_data.is_foreign == "true"
            
        if profile_data.family_status is not None:
            profile.family_status = profile_data.family_status
        
        # 프로필 유형 ID 업데이트
        profile_type_id = get_or_create_profile_type(db, profile_data.dict())
        profile.profile_type_id = profile_type_id
    
    db.commit()
    db.refresh(profile)
    
    return {"message": "프로필이 성공적으로 업데이트되었습니다", "user_id": current_user.id}