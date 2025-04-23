from typing import List, Optional
from openai import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    profiles = relationship("UserProfile", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    chats = relationship("Chat", back_populates="user") 
    saved_policies = relationship("SavedPolicy", back_populates="user", cascade="all, delete-orphan")
    recommended_policies = relationship("RecommendedPolicy", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    region = Column(String(50), nullable=True)
    employment_status = Column(String(50), nullable=True)
    profile_type_id = Column(Integer, ForeignKey("profile_types.id"), nullable=True)
    
    # 추가할 필드들
    is_disabled = Column(Boolean, default=False)  # 장애인 여부
    is_foreign = Column(Boolean, default=False)  # 외국인 여부
    family_status = Column(String(50), nullable=True)  # 가족 상황 (parent, single_parent 등)
    
    interests = Column(JSON, nullable=True)  # 관심 분야 저장
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="profiles")
    profile_type_id = Column(Integer, ForeignKey("profile_types.id"), nullable=True)
    profile_type = relationship("ProfileType")

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    target_age_min = Column(Integer, nullable=True)
    target_age_max = Column(Integer, nullable=True)
    target_gender = Column(String(10), nullable=True)  # 'M', 'F', 'ALL'
    target_region = Column(String(50), nullable=True)
    eligibility = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    application_process = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=True)
    source_page = Column(Integer, nullable=True)  # PDF 페이지 번호
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PolicyChunk(Base):
    __tablename__ = "policy_chunks"
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)  # 특정 정책과 연결될 수 있음
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer, nullable=True)
    vector_id = Column(String(255), nullable=True)  # Pinecone에 저장된 벡터 ID
    chunk_metadata = Column(JSON, nullable=True)  # 추가 메타데이터 (metadata에서 이름 변경)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    type = Column(String(50), nullable=True)  # 'policy_update', 'deadline', 'new_policy'
    related_policy_id = Column(Integer, ForeignKey("policies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="notifications")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    is_user = Column(Integer, default=0)  # 0: 시스템, 1: 사용자
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    chat = relationship("Chat", back_populates="messages")

class ProfileType(Base):
    __tablename__ = "profile_types"
    
    id = Column(Integer, primary_key=True, index=True)
    age_group = Column(String(20), nullable=False)  # '청년', '중장년', '노년'
    gender = Column(String(20), nullable=False)     # '남성', '여성', '기타'
    employment_status = Column(String(20), nullable=False)  # '재직자', '구직자', '자영업자', '학생'
    is_disabled = Column(Boolean, default=False)
    is_foreign = Column(Boolean, default=False)
    family_status = Column(String(50), nullable=False)  # '영유아 자녀 있음', '한부모', '주 양육자', '해당 없음'
    
    # 고유 제약 조건 - 모든 필드의 조합이 고유해야 함
    __table_args__ = (
        UniqueConstraint(
            'age_group', 'gender', 'employment_status', 
            'is_disabled', 'is_foreign', 'family_status',
            name='unique_profile_type'
        ),
    )

class ProfileRecommendation(Base):
    __tablename__ = "profile_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_type_id = Column(Integer, ForeignKey("profile_types.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(String(255), nullable=False)  # Pinecone의 벡터 ID
    policy_title = Column(String(255), nullable=False)
    policy_content = Column(Text, nullable=False)
    page_number = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    relevance_score = Column(Float, nullable=True)
    rank_order = Column(Integer, nullable=False)  # 추천 순위 (1-5)
    
    # 관계 설정
    profile_type = relationship("ProfileType")
    
    # 중복 저장 방지를 위한 유니크 제약 조건
    __table_args__ = (
        UniqueConstraint('profile_type_id', 'rank_order', name='unique_profile_recommendation_rank'),
    )

class RecommendedPolicy(Base):
    __tablename__ = "recommended_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(String(255), nullable=False)  # Pinecone의 벡터 ID
    policy_title = Column(String(255), nullable=False)
    policy_content = Column(Text, nullable=False)
    page_number = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    relevance_score = Column(Float, nullable=True)
    recommended_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="recommended_policies")
    
    # 중복 저장 방지를 위한 유니크 제약 조건
    __table_args__ = (
        UniqueConstraint('user_id', 'policy_id', name='unique_user_policy_rec'),
    )

class SavedPolicy(Base):
    __tablename__ = "saved_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    policy_id = Column(String(255), nullable=False)  # Pinecone의 벡터 ID
    saved_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="saved_policies")
    
    # 중복 저장 방지를 위한 유니크 제약 조건
    __table_args__ = (
        UniqueConstraint('user_id', 'policy_id', name='unique_user_policy'),
    )

class PolicyDisplay(BaseModel):
    id: str
    title: str
    content: str
    page: Optional[str] = None
    category: Optional[str] = None
    is_saved: bool = False
    # 추가된 필드
    enhanced_summary: Optional[str] = None
    enhanced_eligibility: Optional[List[str]] = None
    enhanced_benefits: Optional[List[str]] = None
    enhanced_application: Optional[str] = None