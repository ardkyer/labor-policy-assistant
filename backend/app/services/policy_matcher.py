import os
from typing import List, Dict, Any
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv
import json

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
    
    def generate_user_friendly_policy_summary(self, policy_text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """정책을 사용자 친화적인 형태로 요약합니다."""
        profile_text = "\n".join([f"{k}: {v}" for k, v in profile.items() if v])
        
        prompt = f"""
        다음은 사용자 프로필 정보입니다:
        {profile_text}
        
        다음은 고용노동부 정책 내용입니다:
        {policy_text[:3000]}  # 정책 텍스트 길이 제한
        
        이 정책을 사용자가 이해하기 쉽게 다음 형식으로 요약해주세요:
        1. "summary": 정책의 핵심 내용을 3-4문장으로 요약 (일반인이 이해하기 쉽게)
        2. "benefits": 주요 혜택을 3가지 항목으로 추출 (간결하게 작성)
        3. "eligibility": 지원 대상/신청자격을 2-3가지 항목으로 정리
        4. "application": 신청 방법을 1-2문장으로 간략히 설명
        5. "relevance": 이 사용자에게 이 정책이 왜 유용한지 설명 (1-2문장)
        
        JSON 형식으로 반환해주세요.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 고용노동 정책 전문가입니다. 정책 내용을 일반인이 이해하기 쉽게 요약하는 역할을 합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"정책 요약 생성 중 오류: {str(e)}")
            return {
                "summary": "이 정책은 고용노동부에서 제공하는 지원제도입니다.",
                "benefits": ["정책 혜택을 확인할 수 없습니다."],
                "eligibility": ["지원 대상 정보를 확인할 수 없습니다."],
                "application": "자세한 신청 방법은 관련 기관에 문의하세요.",
                "relevance": "이 정책이 사용자에게 적합한지 평가할 수 없습니다."
            }
    
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
        
        # Pinecone에서 유사한 정책 검색 - 더 많은 결과를 가져옴 (목차 페이지 필터링 후 충분한 결과 확보를 위해)
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k * 3,  # 3배 더 많은 결과 가져오기
            include_metadata=True
        )
        
        # 결과 가공 - 페이지 번호가 20 이하인 항목 제외
        recommendations = []
        for match in results.matches:
            # 페이지 번호 확인
            page = match.metadata.get("page", "0")
            try:
                page_num = int(page)
                # 목차 페이지(1-20) 건너뛰기
                if page_num <= 20:
                    continue
            except (ValueError, TypeError):
                # 페이지 번호를 파싱할 수 없으면 포함
                pass
                
            policy_text = match.metadata.get("text", "")
            
            # 기본 정책 정보
            policy_info = {
                "text": policy_text,
                "page": page,
                "score": match.score,
                "policy_keywords": query, # 생성된 쿼리 키워드도 함께 반환
                "policy_id": match.metadata.get("policy_id", "") or match.id,
                "title": match.metadata.get("title", "") or self.extract_title_from_text(policy_text),
                "category": self.extract_category(policy_text)
            }
            
            # 사용자 친화적인 요약 추가 (시간이 오래 걸리므로 선택적으로 활성화)
            # user_friendly_summary = self.generate_user_friendly_policy_summary(policy_text, profile)
            # policy_info.update(user_friendly_summary)
            
            recommendations.append(policy_info)
            
            # 원하는 개수의 추천 항목을 얻으면 중단
            if len(recommendations) >= top_k:
                break
        
        return recommendations[:top_k]  # 원하는 개수만큼만 반환
    
    def extract_title_from_text(self, text: str) -> str:
        """텍스트에서 제목 추출 (첫번째 유의미한 줄 사용)"""
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) < 100:  # 적당한 길이의 줄 찾기
                return line
        return "제목 없음"
    
    def extract_category(self, text: str) -> str:
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