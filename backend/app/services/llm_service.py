# app/services/llm_service.py
import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv
from typing import List, Dict, Any

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "labor-policy")

class RAGService:
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
    
    def search_similar_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """쿼리와 유사한 청크를 검색합니다."""
        query_embedding = self.get_embedding(query)
        
        # Pinecone에서 유사한 벡터 검색
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return results.matches
    
    def generate_response(self, query: str, user_profile: Dict = None) -> str:
        """쿼리에 대한 응답을 생성합니다."""
        # 유사한 청크 검색
        similar_chunks = self.search_similar_chunks(query)
        
        # 컨텍스트 구성
        context = "\n\n".join([match.metadata["text"] for match in similar_chunks])
        
        # 프롬프트 구성
        prompt = self._build_prompt(query, context, user_profile)
        
        # 응답 생성
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return {
            "answer": response.choices[0].message.content,
            "sources": [{"page": match.metadata.get("page", "N/A"), "text": match.metadata["text"][:200] + "..."} 
                      for match in similar_chunks]
        }
    
    def _build_prompt(self, query: str, context: str, user_profile: Dict = None) -> Dict[str, str]:
        """LLM을 위한 프롬프트를 구성합니다."""
        system_message = """
        당신은 고용노동부의 정책에 대한 지식을 갖춘 도우미입니다. 
        사용자의 질문에 대해 제공된 정책 정보를 바탕으로 정확하고 유용한 답변을 제공해주세요.
        정책 정보에 없는 내용은 모른다고 솔직하게 말하고, 제공된 정보만을 바탕으로 답변해야 합니다.
        사용자의 상황에 맞는 정책을 추천해주되, 항상 출처(페이지 번호)를 포함해 주세요.
        """
        
        user_message = f"질문: {query}\n\n참고 정보:\n{context}"
        
        # 프로필 정보가 있으면 추가
        if user_profile:
            profile_info = "\n".join([f"{k}: {v}" for k, v in user_profile.items()])
            system_message += f"\n\n사용자 프로필 정보:\n{profile_info}\n\n이 정보를 고려하여 사용자에게 맞는 정책 정보를 제공해주세요."
        
        return {
            "system": system_message,
            "user": user_message
        }