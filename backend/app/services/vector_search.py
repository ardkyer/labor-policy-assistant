from typing import Dict, Optional, Any
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