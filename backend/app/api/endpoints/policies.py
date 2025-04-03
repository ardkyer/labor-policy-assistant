from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.db.models import Policy, User
from app.services.policy_matcher import PolicyMatcher
from pydantic import BaseModel

router = APIRouter()

# 정책 매처 초기화
policy_matcher = PolicyMatcher()

class PolicyResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    target_age_min: Optional[int] = None
    target_age_max: Optional[int] = None
    target_gender: Optional[str] = None
    target_region: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    application_process: Optional[str] = None
    source_page: Optional[int] = None

    class Config:
        orm_mode = True

class ProfileModel(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    employment_status: Optional[str] = None
    industry: Optional[str] = None
    region: Optional[str] = None
    interests: Optional[List[str]] = None
    additional_info: Optional[dict] = None

class PolicyRecommendation(BaseModel):
    text: str
    page: str
    score: float
    policy_keywords: str

class RecommendationResponse(BaseModel):
    recommendations: List[PolicyRecommendation]
    profile_summary: str

@router.get("/", response_model=List[PolicyResponse])
def get_policies(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    target_region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    정책 목록 조회 (필터링 가능)
    """
    query = db.query(Policy)
    if category:
        query = query.filter(Policy.category == category)
    if target_region:
        query = query.filter(Policy.target_region == target_region)
    policies = query.offset(skip).limit(limit).all()
    return policies

@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(
    *,
    db: Session = Depends(get_db),
    policy_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    특정 정책 상세 조회
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다")
    return policy

@router.get("/search/", response_model=List[PolicyResponse])
def search_policies(
    *,
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    정책 검색 (타이틀 및 설명 기반)
    """
    policies = db.query(Policy).filter(
        Policy.title.contains(query) | Policy.description.contains(query)
    ).all()
    return policies

@router.get("/recommend/", response_model=List[PolicyResponse])
def recommend_policies_db(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    사용자 프로필 기반 정책 추천 (DB 기반)
    """
    # 사용자 프로필이 있는지 확인
    if not current_user.profiles:
        raise HTTPException(status_code=400, detail="사용자 프로필이 없습니다")
    user_profile = current_user.profiles[0]  # 첫 번째 프로필 사용
    
    # 프로필 기반 간단한 필터링
    query = db.query(Policy)
    
    # 연령 기반 필터링
    if user_profile.age:
        query = query.filter(
            (Policy.target_age_min.is_(None) | (Policy.target_age_min <= user_profile.age)) &
            (Policy.target_age_max.is_(None) | (Policy.target_age_max >= user_profile.age))
        )
    
    # 성별 기반 필터링
    if user_profile.gender:
        query = query.filter(
            (Policy.target_gender.is_(None)) |
            (Policy.target_gender == "ALL") |
            (Policy.target_gender == user_profile.gender)
        )
    
    # 지역 기반 필터링
    if user_profile.region:
        query = query.filter(
            (Policy.target_region.is_(None)) |
            (Policy.target_region == user_profile.region)
        )
    
    policies = query.all()
    return policies

@router.post("/recommend-vector/", response_model=RecommendationResponse)
async def recommend_policies_vector(
    profile: ProfileModel,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    사용자 프로필에 기반하여 벡터 검색으로 정책을 추천합니다.
    """
    try:
        # 프로필 딕셔너리로 변환
        profile_dict = profile.dict(exclude_none=True)
        
        # 프로필 요약 생성 (Null 값 제외)
        profile_summary = "\n".join([f"{k}: {v}" for k, v in profile_dict.items() if v])
        
        # 정책 추천
        recommendations = policy_matcher.recommend_policies(profile_dict)
        
        return {
            "recommendations": recommendations,
            "profile_summary": profile_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))