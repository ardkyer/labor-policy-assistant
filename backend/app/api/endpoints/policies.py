from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models import Policy, User
from pydantic import BaseModel

router = APIRouter()

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
def recommend_policies(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    사용자 프로필 기반 정책 추천
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