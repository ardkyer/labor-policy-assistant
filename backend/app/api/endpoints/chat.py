from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.db.models import User, Policy, PolicyChunk
from app.services.llm_service import RAGService

router = APIRouter()

# RAG 서비스 초기화
rag_service = RAGService()

class ChatRequest(BaseModel):
    query: str
    user_profile: Optional[dict] = None

class Source(BaseModel):
    page: str
    text: str
    similarity: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []

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
        # 사용자 프로필 정보 추가 (있는 경우)
        user_profile = None
        if current_user.profiles and len(current_user.profiles) > 0:
            profile = current_user.profiles[0]
            user_profile = {
                "age": profile.age,
                "gender": profile.gender,
                "employment_status": profile.employment_status,
                "region": profile.region
            }
        
        # 요청에 프로필이 포함된 경우 사용
        if chat_request.user_profile:
            user_profile = chat_request.user_profile
        
        # RAG 서비스를 통한 응답 생성
        response = rag_service.generate_response(query, user_profile)
        
        # 응답 형식 변환
        sources_formatted = []
        for source in response["sources"]:
            sources_formatted.append(
                Source(
                    page=source["page"],
                    text=source["text"],
                    similarity=source.get("score")
                )
            )
        
        return {
            "answer": response["answer"],
            "sources": sources_formatted
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 오류: {str(e)}")