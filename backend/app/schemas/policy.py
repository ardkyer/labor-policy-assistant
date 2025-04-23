from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SavedPolicyBase(BaseModel):
    policy_id: str

class SavedPolicyCreate(SavedPolicyBase):
    pass

class SavedPolicyResponse(SavedPolicyBase):
    id: int
    user_id: int
    saved_at: datetime
    
    class Config:
        orm_mode = True

class RecommendedPolicyBase(BaseModel):
    policy_id: str
    policy_title: str
    policy_content: str
    page_number: Optional[str] = None
    category: Optional[str] = None
    relevance_score: Optional[float] = None

class RecommendedPolicyCreate(RecommendedPolicyBase):
    pass

class RecommendedPolicyResponse(RecommendedPolicyBase):
    id: int
    user_id: int
    recommended_at: datetime
    
    class Config:
        orm_mode = True

# 프론트엔드에 반환할 정책 데이터 형식
class PolicyDisplay(BaseModel):
    id: str  # policy_id
    title: str
    content: str
    page: Optional[str] = None
    category: Optional[str] = None
    is_saved: bool = False
    
    class Config:
        orm_mode = True