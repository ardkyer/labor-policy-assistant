from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.db.models import User, Policy, PolicyChunk, Chat, ChatMessage 
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
    

@router.post("/create", response_model=dict)
async def create_new_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """새 채팅 생성"""
    
    # 새 채팅 생성
    new_chat = Chat(
        user_id=current_user.id,
        title="새 대화"  # 기본 제목
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    return {
        "id": new_chat.id,
        "title": new_chat.title,
        "created_at": new_chat.created_at
    }

@router.get("/list", response_model=List[dict])
async def get_chat_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """사용자의 채팅 목록 조회"""
    
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).order_by(Chat.created_at.desc()).all()
    
    result = []
    for chat in chats:
        # 각 채팅의 첫 메시지를 제목으로 사용
        first_message = db.query(ChatMessage)\
            .filter(ChatMessage.chat_id == chat.id, ChatMessage.is_user == 1)\
            .order_by(ChatMessage.created_at).first()
            
        title = chat.title
        if first_message and not title:
            # 첫 메시지의 일부를 제목으로 설정 (너무 길면 자름)
            title = first_message.content[:30] + "..." if len(first_message.content) > 30 else first_message.content
            
        result.append({
            "id": chat.id,
            "title": title,
            "created_at": chat.created_at.isoformat()
        })
    
    return result

@router.get("/{chat_id}/messages", response_model=List[dict])
async def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """특정 채팅의 메시지 목록 조회"""
    
    # 해당 채팅이 현재 사용자의 것인지 확인
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    
    messages = db.query(ChatMessage)\
        .filter(ChatMessage.chat_id == chat_id)\
        .order_by(ChatMessage.created_at).all()
    
    result = []
    for message in messages:
        result.append({
            "id": message.id,
            "content": message.content,
            "is_user": message.is_user == 1,
            "sources": message.sources,
            "created_at": message.created_at.isoformat()
        })
    
    return result

@router.post("/{chat_id}/message", response_model=ChatResponse)
async def add_message_to_chat(
    chat_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """채팅에 새 메시지 추가 및 응답 생성"""
    
    # 해당 채팅이 현재 사용자의 것인지 확인
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    
    query = chat_request.query
    
    # 사용자 메시지 저장
    user_message = ChatMessage(
        chat_id=chat_id,
        is_user=1,
        content=query,
        sources=None
    )
    db.add(user_message)
    db.commit()
    
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
        
        # 응답 저장
        assistant_message = ChatMessage(
            chat_id=chat_id,
            is_user=0,
            content=response["answer"],
            sources=response["sources"]
        )
        db.add(assistant_message)
        
        # 첫 메시지라면 채팅 제목 업데이트
        messages_count = db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).count()
        if messages_count <= 2:  # 사용자 메시지와 시스템 응답을 합쳐 2개
            chat.title = query[:30] + "..." if len(query) > 30 else query
            db.add(chat)
            
        db.commit()
        
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
        db.rollback()
        raise HTTPException(status_code=500, detail=f"챗봇 오류: {str(e)}")

@router.delete("/{chat_id}", response_model=dict)
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """채팅 삭제"""
    
    # 해당 채팅이 현재 사용자의 것인지 확인
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="채팅을 찾을 수 없습니다.")
    
    # 채팅 관련 메시지 먼저 삭제
    db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).delete()
    
    # 채팅 삭제
    db.delete(chat)
    db.commit()
    
    return {"message": "채팅이 성공적으로 삭제되었습니다."}