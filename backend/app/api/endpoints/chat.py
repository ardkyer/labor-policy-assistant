from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pinecone
import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.db.models import User, Policy, PolicyChunk

router = APIRouter()

# OpenAI 및 Pinecone 초기화
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

pinecone.init(
    api_key=settings.PINECONE_API_KEY,
    environment=settings.PINECONE_ENVIRONMENT
)

index = pinecone.Index(settings.PINECONE_INDEX_NAME)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []

@router.post("/", response_model=ChatResponse)
async def chat_with_assistant(
    *,
    db: Session = Depends(get_db),
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    고용노동 정책 어시스턴트와 대화
    """
    query = chat_request.query
    
    try:
        # 1. 쿼리 임베딩 생성
        query_embedding = embeddings.embed_query(query)
        
        # 2. Pinecone에서 유사한 청크 검색
        search_results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )
        
        # 3. 검색 결과에서 관련 정보 추출
        contexts = []
        sources = []
        
        for match in search_results['matches']:
            if match['score'] < 0.7:  # 유사도 임계값
                continue
                
            context = match['metadata']['text']
            page_number = match['metadata'].get('page', 'N/A')
            
            contexts.append(context)
            sources.append({
                "page": page_number,
                "text": context[:150] + "..." if len(context) > 150 else context,
                "similarity": match['score']
            })
        
        # 4. 컨텍스트 기반 응답 생성
        if contexts:
            prompt = f"""
            당신은 고용노동부 정책 전문가입니다. 다음 정보를 기반으로 사용자의 질문에 정확하게 답변해주세요.
            
            ### 관련 정책 정보:
            {' '.join(contexts)}
            
            ### 사용자 질문:
            {query}
            
            정확한 정보만 제공하고, 모르는 내용은 모른다고 답변하세요. 관련 페이지 번호도 언급해주세요.
            """
            
            llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
            answer = llm.predict(prompt)
        else:
            answer = "죄송합니다, 귀하의 질문에 관련된 정책 정보를 찾을 수 없습니다. 다른 질문을 해주시거나 더 구체적인 내용을 알려주세요."
        
        return {
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 오류: {str(e)}")