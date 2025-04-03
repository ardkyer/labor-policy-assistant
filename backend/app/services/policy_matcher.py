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
        # 프로필 기반 쿼리 생성을 위한 LLM 호출
        profile_text = "\n".join([f"{k}: {v}" for k, v in profile.items() if v])
        
        prompt = f"""
        다음은 사용자 프로필 정보입니다:
        {profile_text}
        
        이 사용자에게 관련될 수 있는 고용노동 정책을 찾기 위한 검색어를 생성해주세요.
        사용자의 연령, 고용 상태, 산업 분야, 요구사항 등을 고려하여 작성하세요.
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