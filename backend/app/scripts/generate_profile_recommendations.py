# app/scripts/generate_profile_recommendations.py

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

# 올바른 경로에서 SessionLocal 임포트
from app.db.base import SessionLocal
from app.db.models import ProfileType, ProfileRecommendation
from app.services.policy_matcher import PolicyMatcher
from tqdm import tqdm

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

def generate_profile_recommendations():
    """모든 프로필 타입에 대한 추천 정책 생성"""
    db = SessionLocal()
    policy_matcher = PolicyMatcher()
    
    try:
        # 모든 프로필 타입 가져오기
        profile_types = db.query(ProfileType).all()
        
        if not profile_types:
            print("프로필 타입이 없습니다. 먼저 프로필 타입을 생성해주세요.")
            return
        
        print(f"{len(profile_types)}개 프로필 타입에 대한 추천 정책 생성을 시작합니다...")
        
        for i, profile_type in enumerate(tqdm(profile_types)):
            # 기존 추천 삭제
            db.query(ProfileRecommendation).filter(
                ProfileRecommendation.profile_type_id == profile_type.id
            ).delete()
            
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
            
            recommendations = policy_matcher.recommend_policies(profile_dict, top_k=5)

            # 만약 위에서 필터링이 적용되지 않았거나 추가 필터링이 필요한 경우:
            filtered_recommendations = []
            for rec in recommendations:
                # 페이지 번호 확인
                page = rec.get("page", "0")
                try:
                    page_num = int(page)
                    # 목차 페이지(1-20) 건너뛰기
                    if page_num <= 20:
                        continue
                except (ValueError, TypeError):
                    pass
                
                filtered_recommendations.append(rec)

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
        
        print("모든 프로필 타입에 대한 추천 정책 생성이 완료되었습니다!")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_profile_recommendations()