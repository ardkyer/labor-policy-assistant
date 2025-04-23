from typing import Dict, Optional, Any, List
from pinecone import Pinecone
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "labor-policy")

def get_policy_by_id(policy_id: str) -> Optional[Dict[str, Any]]:
    """정책 ID로 정책 정보 가져오기"""
    try:
        # Pinecone에서 벡터 ID로 검색
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        
        # 해당 ID의 벡터 조회
        result = index.fetch(ids=[policy_id])
        
        if policy_id in result.vectors:
            vector = result.vectors[policy_id]
            text = vector.metadata.get("text", "")
            
            # 제목 추출
            title = extract_title_from_text(text)
            
            return {
                "id": policy_id,
                "title": title,
                "content": text,
                "page": vector.metadata.get("page"),
                "category": extract_category(text)
            }
        return None
    except Exception as e:
        print(f"정책 조회 오류: {str(e)}")
        return None

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

def search_policies(query: str, top_k: int = 5, user_profile: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """정책 검색 및 결과 가공"""
    try:
        # Pinecone 초기화
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(INDEX_NAME)
        
        # 임베딩 생성 (OpenAI API 호출 필요)
        from app.services.policy_matcher import PolicyMatcher
        policy_matcher = PolicyMatcher()
        query_embedding = policy_matcher.get_embedding(query)
        
        # 벡터 검색
        results = index.query(
            vector=query_embedding,
            top_k=top_k * 2,  # 목차 페이지 필터링 위해 더 많이 가져옴
            include_metadata=True
        )
        
        # 결과 가공
        search_results = []
        for match in results.matches:
            # 페이지 번호 확인 (목차 페이지 건너뛰기)
            page = match.metadata.get("page", "0")
            try:
                page_num = int(page)
                if page_num <= 20:  # 목차 페이지 건너뛰기
                    continue
            except (ValueError, TypeError):
                pass
                
            policy_text = match.metadata.get("text", "")
            
            # 기본 정보
            policy_info = {
                "id": match.id,
                "content": policy_text,
                "page": match.metadata.get("page", ""),
                "score": match.score,
                "title": match.metadata.get("title", "") or extract_title_from_text(policy_text),
                "category": extract_category(policy_text)
            }
            
            search_results.append(policy_info)
            
            # 원하는 개수만큼 정책 가져오기
            if len(search_results) >= top_k:
                break
        
        return search_results
    except Exception as e:
        print(f"정책 검색 오류: {str(e)}")
        return []