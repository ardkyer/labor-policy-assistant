import json
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.models import User, SavedPolicy, RecommendedPolicy, UserProfile
from app.services.policy_matcher import PolicyMatcher
from openai import OpenAI

policy_matcher = PolicyMatcher()

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

def create_user_policy_recommendations(db: Session, user_id: int) -> List[RecommendedPolicy]:
    """사용자 프로필 기반으로 정책 추천 생성 및 저장"""
    # 1. 사용자 프로필 가져오기
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not user_profile:
        return []
    
    # 2. 프로필을 딕셔너리로 변환
    profile_dict = {
        "age": user_profile.age,
        "gender": user_profile.gender,
        "employment_status": user_profile.employment_status,
        "region": user_profile.region,
        "is_disabled": user_profile.is_disabled,
        "is_foreign": user_profile.is_foreign,
        "family_status": user_profile.family_status
    }
    
    # 3. 프로필에 기반한 정책 추천 가져오기
    recommendations = policy_matcher.recommend_policies(profile_dict, top_k=5)
    
    # 4. 기존 추천 정책 삭제 (새로 갱신)
    db.query(RecommendedPolicy).filter(RecommendedPolicy.user_id == user_id).delete()
    
    # 5. 추천 정책 저장
    recommended_policies = []
    for rec in recommendations:
        policy_text = rec.get("text", "")
        policy_title = rec.get("title") or extract_title_from_text(policy_text)
        
        recommended_policy = RecommendedPolicy(
            user_id=user_id,
            policy_id=rec.get("id", "") or rec.get("policy_id", ""),
            policy_title=policy_title,
            policy_content=policy_text,
            page_number=rec.get("page", ""),
            category=rec.get("category") or extract_category(policy_text),
            relevance_score=rec.get("score", 0.0)
        )
        
        db.add(recommended_policy)
        recommended_policies.append(recommended_policy)
    
    db.commit()
    return recommended_policies

def get_user_recommended_policies(db: Session, user_id: int) -> List[RecommendedPolicy]:
    """사용자에게 추천된 정책 목록 가져오기"""
    recommendations = db.query(RecommendedPolicy).filter(
        RecommendedPolicy.user_id == user_id
    ).all()
    
    # 추천 목록이 없으면 새로 생성
    if not recommendations:
        recommendations = create_user_policy_recommendations(db, user_id)
    
    return recommendations

def save_policy(db: Session, user_id: int, policy_id: str) -> SavedPolicy:
    """사용자가 정책을 관심 목록에 저장"""
    existing = db.query(SavedPolicy).filter(
        SavedPolicy.user_id == user_id,
        SavedPolicy.policy_id == policy_id
    ).first()
    
    if existing:
        return existing
    
    saved_policy = SavedPolicy(
        user_id=user_id,
        policy_id=policy_id
    )
    
    db.add(saved_policy)
    db.commit()
    db.refresh(saved_policy)
    
    return saved_policy

def unsave_policy(db: Session, user_id: int, policy_id: str) -> bool:
    """사용자가 정책을 관심 목록에서 제거"""
    result = db.query(SavedPolicy).filter(
        SavedPolicy.user_id == user_id,
        SavedPolicy.policy_id == policy_id
    ).delete()
    
    db.commit()
    return result > 0

def get_saved_policies(db: Session, user_id: int) -> List[SavedPolicy]:
    """사용자가 저장한 관심 정책 목록 가져오기"""
    return db.query(SavedPolicy).filter(
        SavedPolicy.user_id == user_id
    ).all()

def is_policy_saved(db: Session, user_id: int, policy_id: str) -> bool:
    """정책이 사용자의 관심 목록에 저장되어 있는지 확인"""
    return db.query(SavedPolicy).filter(
        SavedPolicy.user_id == user_id,
        SavedPolicy.policy_id == policy_id
    ).first() is not None

def generate_user_friendly_policy_description(policy_text: str, user_profile: dict) -> dict:
    """정책 텍스트를 사용자 친화적인 형태로 변환"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    다음은 고용노동부 정책 내용입니다:
    {policy_text[:2000]}  # 긴 정책은 앞부분만 사용
    
    다음 정보를 추출해서 JSON 형식으로 반환해주세요:
    1. "summary": 이 정책의 핵심 내용을 3-4문장으로 요약 (일반인이 이해하기 쉽게)
    2. "benefits": 이 정책의 주요 혜택을 3가지 항목으로 추출 (간결하게 작성)
    3. "eligibility": 이 정책의 대상자/신청자격을 2-3가지 항목으로 정리
    4. "application": 신청 방법을 1-2문장으로 간략히 설명
    
    사용자 프로필: {user_profile}
    이 사용자에게 어떻게 도움이 될 수 있는지 고려해서 작성해주세요.
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 고용노동부 정책을 일반인이 이해하기 쉽게 설명해주는 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        # JSON 파싱
        result = json.loads(response.choices[0].message.content)
        return result
    except:
        # 파싱 실패시 기본값 반환
        return {
            "summary": "정책 요약을 생성할 수 없습니다.",
            "benefits": ["혜택 정보를 찾을 수 없습니다."],
            "eligibility": ["자격 요건 정보를 찾을 수 없습니다."],
            "application": "신청 방법 정보를 찾을 수 없습니다."
        }