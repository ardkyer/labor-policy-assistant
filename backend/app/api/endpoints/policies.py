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
    age: Optional[str] = None,
    gender: Optional[str] = None,
    employment: Optional[str] = None,
    region: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    사용자 프로필 기반 정책 추천 (필터 기반)
    """
    # 1. 쿼리 파라미터에서 필터 정보 가져오기
    filters = {
        "age": age,
        "gender": gender,
        "employment_status": employment,
        "region": region
    }
    
    # 2. 필터 정보가 없는 경우 사용자 프로필에서 정보 사용
    if not any(filters.values()) and current_user.profiles:
        user_profile = current_user.profiles[0]
        filters = {
            "age": user_profile.age,
            "gender": user_profile.gender,
            "employment_status": user_profile.employment_status,
            "region": user_profile.region
        }
    
    # 3. 벡터 검색 사용하여 정책 추천
    try:
        # 필터에서 None 값 제거
        clean_filters = {k: v for k, v in filters.items() if v}
        
        # 벡터 기반 정책 추천
        recommendations = policy_matcher.recommend_policies(clean_filters)
        
        # 결과 변환
        policies = []
        for recommendation in recommendations:
            # DB에서 정책 정보 찾기 (있는 경우)
            policy_id = recommendation.get("policy_id")
            policy = None
            if policy_id:
                policy = db.query(Policy).filter(Policy.id == policy_id).first()
            
            # 정책 정보가 없으면 벡터 검색 결과로 생성
            if policy:
                policies.append(policy)
            else:
                # 가상 정책 객체 생성
                policies.append(Policy(
                    id=0,  # 임시 ID
                    title=recommendation.get("title", "추천 정책"),
                    description=recommendation.get("text", ""),
                    source_page=recommendation.get("page", "")
                ))
        
        return policies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 추천 중 오류 발생: {str(e)}")

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