from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_optional, get_db, get_current_user
from app.db.models import Policy, ProfileRecommendation, User, UserProfile
from app.services.policy_matcher import PolicyMatcher
from pydantic import BaseModel
from app.schemas.policy import PolicyDisplay
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

from app.services.policy_service import (
    get_user_recommended_policies, 
    save_policy, 
    unsave_policy, 
    get_saved_policies,
    is_policy_saved,
    create_user_policy_recommendations
)

# .env 파일에서 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter()

# OpenAI 클라이언트 초기화
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
        from_attributes = True

class PolicyEnhanceRequest(BaseModel):
    policy_id: str
    policy_content: str

class PolicyEnhanceResponse(BaseModel):
    policy_id: str
    summary: str
    eligibility: List[str]
    benefits: List[str]
    application: str

class ProfileModel(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    employment_status: Optional[str] = None
    industry: Optional[str] = None
    region: Optional[str] = None
    interests: Optional[List[str]] = None
    additional_info: Optional[dict] = None
    # 추가된 필드들
    is_disabled: Optional[bool] = None
    is_foreign: Optional[bool] = None
    family_status: Optional[str] = None

class PolicyRecommendation(BaseModel):
    text: str
    page: str
    score: float
    policy_keywords: str

class RecommendationResponse(BaseModel):
    recommendations: List[PolicyRecommendation]
    profile_summary: str

def generate_user_friendly_policy_description(policy_text: str, user_profile: Optional[Dict] = None) -> Dict:
    """정책 텍스트를 사용자 친화적인 형태로 변환"""
    try:
        # 프로필 정보가 있으면 사용자 맞춤형 설명 추가
        profile_context = ""
        if user_profile:
            profile_context = f"""
            다음은 사용자 프로필 정보입니다:
            {json.dumps(user_profile, ensure_ascii=False, indent=2)}
            
            위 사용자에게 이 정책이 어떻게 도움이 될 수 있는지 고려하여 설명해주세요.
            """
        
        prompt = f"""
        다음은 고용노동부 정책 내용입니다:
        {policy_text[:3000]}  # 정책 텍스트 길이 제한
        
        다음 정보를 추출해서 JSON 형식으로 반환해주세요:
        1. "summary": 이 정책의 핵심 내용을 3-4문장으로 요약 (일반인이 이해하기 쉽게)
        2. "eligibility": 이 정책의 대상자/신청자격을 2-4가지 항목으로 정리 (리스트 형식)
        3. "benefits": 이 정책의 주요 혜택을 2-4가지 항목으로 추출 (리스트 형식)
        4. "application": 신청 방법을 1-2문장으로 간략히 설명
        
        {profile_context}
        
        JSON 형식으로 반환해주세요. 각 항목은 간결하고 이해하기 쉽게 작성해주세요.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 고용노동부 정책을 일반인이 이해하기 쉽게 설명해주는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # JSON 파싱
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"정책 설명 생성 오류: {str(e)}")
        # 파싱 실패시 기본값 반환
        return {
            "summary": "이 정책은 고용노동부에서 제공하는 지원 제도입니다. 자세한 내용은 상세 정보를 확인해주세요.",
            "eligibility": ["해당 정책의 지원 대상 정보를 확인할 수 없습니다."],
            "benefits": ["해당 정책의 혜택 정보를 확인할 수 없습니다."],
            "application": "자세한 신청 방법은 고용노동부 홈페이지나 관련 기관에 문의하세요."
        }

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

@router.post("/enhance", response_model=PolicyEnhanceResponse)
async def enhance_policy_description(
    request: PolicyEnhanceRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> Any:
    """
    정책 설명을 LLM을 사용하여 사용자 친화적으로 변환
    """
    # 사용자 프로필 정보 가져오기
    profile_dict = None
    
    if current_user:
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if user_profile:
            # 프로필 정보를 딕셔너리로 변환
            profile_dict = {
                "age": user_profile.age,
                "gender": user_profile.gender,
                "employment_status": user_profile.employment_status,
                "region": user_profile.region,
                "is_disabled": user_profile.is_disabled,
                "is_foreign": user_profile.is_foreign,
                "family_status": user_profile.family_status
            }
    
    # LLM으로 정책 설명 생성
    enhanced_description = generate_user_friendly_policy_description(
        request.policy_content, profile_dict
    )
    
    # 결과에 정책 ID 추가
    enhanced_description["policy_id"] = request.policy_id
    
    return PolicyEnhanceResponse(**enhanced_description)

@router.get("/search/", response_model=List[PolicyDisplay])
def search_policies(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> Any:
    """
    사용자 친화적인 정책 검색 (벡터 검색 + LLM 요약)
    """
    # 사용자 프로필 정보 (로그인한 경우)
    user_profile = None
    if current_user:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if profile:
            user_profile = {
                "age": profile.age,
                "gender": profile.gender,
                "employment_status": profile.employment_status,
                "region": profile.region,
                "is_disabled": profile.is_disabled,
                "is_foreign": profile.is_foreign,
                "family_status": profile.family_status
            }
    
    try:
        # 벡터 검색 사용
        query_embedding = policy_matcher.get_embedding(q)
        search_results = policy_matcher.index.query(
            vector=query_embedding,
            top_k=10,
            include_metadata=True
        )
        
        # 저장된 정책 ID 목록 (로그인한 경우)
        saved_policy_ids = set()
        if current_user:
            saved_policies = get_saved_policies(db, current_user.id)
            saved_policy_ids = {p.policy_id for p in saved_policies}
        
        # 결과 가공 및 동시에 모든 정책에 대해 LLM 요약 생성
        policies = []
        
        for match in search_results.matches:
            # 페이지 번호 확인 (목차 페이지 건너뛰기)
            page = match.metadata.get("page", "0")
            try:
                page_num = int(page)
                if page_num <= 20:  # 목차 페이지 건너뛰기
                    continue
            except (ValueError, TypeError):
                pass
                
            policy_text = match.metadata.get("text", "")
            
            # 제목 추출
            title = match.metadata.get("title", "") or policy_matcher.extract_title_from_text(policy_text)
            
            # 카테고리 추출
            category = match.metadata.get("category", "") or policy_matcher.extract_category(policy_text)
            
            # 모든 정책에 대해 LLM 처리
            try:
                # LLM으로 정책 요약 생성 (동기적 처리)
                summary_result = generate_user_friendly_policy_description(policy_text[:3000], user_profile)
                
                # PolicyDisplay 객체 생성
                policy_info = PolicyDisplay(
                    id=match.id,
                    title=title,
                    content=policy_text,
                    page=page,
                    category=category,
                    is_saved=match.id in saved_policy_ids,
                    # LLM으로 생성된 향상된 정보
                    enhanced_summary=summary_result.get("summary", ""),
                    enhanced_eligibility=summary_result.get("eligibility", []),
                    enhanced_benefits=summary_result.get("benefits", []),
                    enhanced_application=summary_result.get("application", "")
                )
                
                policies.append(policy_info)
                
                # 최대 6개 정책만 처리
                if len(policies) >= 6:
                    break
                    
            except Exception as e:
                # LLM 처리 실패 시 기본 정보만 포함
                print(f"정책 요약 생성 오류: {str(e)}")
                policy_info = PolicyDisplay(
                    id=match.id,
                    title=title,
                    content=policy_text,
                    page=page,
                    category=category,
                    is_saved=match.id in saved_policy_ids
                )
                policies.append(policy_info)
                
                # 최대 6개 정책만 처리
                if len(policies) >= 6:
                    break
        
        return policies
        
    except Exception as e:
        # 오류 발생 시 원인 로깅 후 예외 발생
        print(f"정책 검색 오류 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=f"정책 검색 중 오류 발생")

@router.get("/recommend/", response_model=List[PolicyDisplay])
def recommend_policies_llm(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    사용자 프로필 기반 맞춤형 정책 추천 (LLM 향상)
    """
    # 사용자 프로필 정보 가져오기
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not user_profile:
        raise HTTPException(status_code=404, detail="프로필 정보가 없습니다")
    
    # 프로필을 딕셔너리로 변환
    profile_dict = {
        "age": user_profile.age,
        "gender": user_profile.gender,
        "employment_status": user_profile.employment_status,
        "region": user_profile.region,
        "is_disabled": user_profile.is_disabled,
        "is_foreign": user_profile.is_foreign,
        "family_status": user_profile.family_status
    }
    
    try:
        # 정책 추천 가져오기
        recommendations = policy_matcher.recommend_policies(profile_dict, top_k=6)
        
        # 저장된 정책 ID 목록
        saved_policy_ids = {p.policy_id for p in get_saved_policies(db, current_user.id)}
        
        # 결과 가공
        result = []
        for rec in recommendations:
            # 기본 정보
            policy = PolicyDisplay(
                id=rec.get("policy_id", ""),
                title=rec.get("title", "정책 제목을 찾을 수 없습니다"),
                content=rec.get("text", ""),
                page=rec.get("page", ""),
                category=rec.get("category", "기타"),
                is_saved=rec.get("policy_id", "") in saved_policy_ids
            )
            
            result.append(policy)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 추천 중 오류 발생: {str(e)}")

@router.get("/recommended/", response_model=List[PolicyDisplay])
def get_recommended_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자 프로필 유형에 기반한 미리 계산된 추천 정책 가져오기"""
    # 사용자 프로필 가져오기
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not user_profile or not user_profile.profile_type_id:
        raise HTTPException(status_code=404, detail="프로필 정보가 없습니다")
    
    # 프로필 유형에 맞는 미리 계산된 추천 가져오기
    recommendations = db.query(ProfileRecommendation).filter(
        ProfileRecommendation.profile_type_id == user_profile.profile_type_id
    ).order_by(ProfileRecommendation.rank_order).all()
    
    # 저장된 정책 ID 목록 가져오기
    saved_policy_ids = {
        p.policy_id for p in get_saved_policies(db, current_user.id)
    }
    
    # 반환 형식으로 변환
    result = []
    for rec in recommendations:
        result.append(PolicyDisplay(
            id=rec.policy_id,
            title=rec.policy_title,
            content=rec.policy_content,
            page=rec.page_number,
            category=rec.category,
            is_saved=rec.policy_id in saved_policy_ids
        ))
    
    return result

@router.post("/refresh-recommendations/", status_code=status.HTTP_200_OK)
def refresh_recommended_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자 추천 정책 강제 갱신"""
    create_user_policy_recommendations(db, current_user.id)
    return {"message": "추천 정책이 갱신되었습니다."}

@router.post("/save/{policy_id}", status_code=status.HTTP_200_OK)
def save_user_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """정책을 사용자의 관심 목록에 저장"""
    save_policy(db, current_user.id, policy_id)
    return {"message": "정책이 저장되었습니다."}

@router.delete("/save/{policy_id}", status_code=status.HTTP_200_OK)
def unsave_user_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """정책을 사용자의 관심 목록에서 제거"""
    success = unsave_policy(db, current_user.id, policy_id)
    if not success:
        raise HTTPException(status_code=404, detail="저장된 정책을 찾을 수 없습니다.")
    return {"message": "정책이 관심 목록에서 제거되었습니다."}

@router.get("/saved/", response_model=List[PolicyDisplay])
def get_user_saved_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자가 저장한 관심 정책 목록 가져오기"""
    from app.services.vector_search import get_policy_by_id
    
    saved_policies = get_saved_policies(db, current_user.id)
    
    result = []
    for saved in saved_policies:
        policy_data = get_policy_by_id(saved.policy_id)
        if policy_data:
            result.append(PolicyDisplay(
                id=saved.policy_id,
                title=policy_data.get("title", "제목 없음"),
                content=policy_data.get("content", ""),
                page=policy_data.get("page"),
                category=policy_data.get("category", "기타"),
                is_saved=True
            ))
    
    return result

@router.get("/profiles/me/saved-policies", response_model=List[PolicyDisplay])
def get_my_saved_policies_alias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_saved_policies(db, current_user)
