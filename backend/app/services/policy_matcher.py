# app/services/policy_matcher.py
import os
from typing import List, Dict, Any
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "labor-policy")

class PolicyMatcher:
    def __init__(self):
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Pinecone 초기화
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(INDEX_NAME)
    
    def get_embedding(self, text: str) -> List[float]:
        """텍스트에 대한 임베딩 벡터를 생성합니다."""
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def profile_to_query(self, profile: Dict[str, Any]) -> str:
        """사용자 프로필을 쿼리 문자열로 변환합니다."""
        # 카테고리 분류를 위한 설명 추가
        profile_categories = []
        
        # 연령 기반 카테고리
        if profile.get("age"):
            age = int(profile.get("age", 0))
            if age < 35:
                profile_categories.append("청년")
            elif age >= 50:
                profile_categories.append("고령자/신중년")
        
        # 다른 특성 기반 카테고리
        if profile.get("is_disabled") == True:
            profile_categories.append("장애인")
        
        if profile.get("gender") == "female":
            profile_categories.append("여성")
            
        if profile.get("family_status") in ["parent", "single_parent"]:
            profile_categories.append("육아지원")
        
        if profile.get("is_foreign") == True:
            profile_categories.append("외국인근로자")
        
        if profile.get("employment_status") == "business":
            profile_categories.append("사업주")
        
        # 카테고리 문자열 생성
        categories_str = ", ".join(profile_categories) if profile_categories else "해당 없음"
        
        # 프로필 텍스트 구성
        profile_text = f"""
        연령: {profile.get('age', '정보 없음')}
        성별: {profile.get('gender', '정보 없음')}
        고용상태: {profile.get('employment_status', '정보 없음')}
        장애인 여부: {'예' if profile.get('is_disabled') else '아니오'}
        외국인 여부: {'예' if profile.get('is_foreign') else '아니오'}
        가족 상황: {profile.get('family_status', '정보 없음')}
        관련 정책 카테고리: {categories_str}
        """
        
        # LLM 프롬프트 구성
        prompt = f"""
        다음은 사용자 프로필 정보입니다:
        {profile_text}
        
        이 사용자에게 관련될 수 있는 고용노동 정책을 찾기 위한 검색어를 생성해주세요.
        사용자에게 해당되는 다음 카테고리 중 관련 항목을 고려하세요: {categories_str}
        
        사용자의 연령, 고용 상태, 특수 상황(장애, 외국인, 가족 상황 등)을 고려하여 작성하세요.
        검색어만 작성하고 다른 설명은 포함하지 마세요.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 사용자 프로필을 분석하여 관련 고용노동 정책을 찾기 위한 키워드를 생성하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_relevance_explanation(self, profile: Dict[str, Any], policy_text: str) -> str:
        """정책과 사용자 프로필 간의 연관성 설명을 생성합니다."""
        profile_text = "\n".join([f"{k}: {v}" for k, v in profile.items() if v])
        
        prompt = f"""
        다음은 사용자 프로필 정보입니다:
        {profile_text}
        
        다음은 추천된 정책 정보입니다:
        {policy_text}
        
        위 정책이 이 사용자에게 어떻게 도움이 될 수 있는지 2-3문장으로 간략히 설명해주세요.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 고용노동 정책 전문가입니다. 사용자에게 맞춤형 정책 추천을 제공합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        return response.choices[0].message.content.strip()
    
    def recommend_policies(self, profile: Dict[str, Any], top_k: int = 5) -> List[Dict[str, Any]]:
        """사용자 프로필에 기반하여 정책을 추천합니다."""
        # 프로필을 쿼리로 변환
        query = self.profile_to_query(profile)
        
        # 쿼리 임베딩 생성
        query_embedding = self.get_embedding(query)
        
        # Pinecone에서 유사한 정책 검색
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # 결과 가공
        recommendations = []
        for match in results.matches:
            policy_text = match.metadata.get("text", "")
            
            # 추가: 연관성 설명 생성 (선택 사항, API 호출을 늘리므로 필요에 따라 사용)
            # relevance = self.generate_relevance_explanation(profile, policy_text)
            
            recommendations.append({
                "text": policy_text,
                "page": match.metadata.get("page", "정보 없음"),
                "score": match.score,
                "policy_keywords": query, # 생성된 쿼리 키워드도 함께 반환
                "policy_id": match.metadata.get("policy_id", ""),
                "title": match.metadata.get("title", "")
                # "relevance": relevance  # 선택 사항
            })
        
        return recommendations