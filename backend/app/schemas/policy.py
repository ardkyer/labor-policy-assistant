from pydantic import BaseModel, Field
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

class PolicyDisplay(BaseModel):
    id: str
    title: str
    content: str
    page: Optional[str] = None
    category: Optional[str] = None
    is_saved: bool = False
    # 추가된 필드
    enhanced_summary: Optional[str] = None
    enhanced_eligibility: Optional[List[str]] = Field(default_factory=list)
    enhanced_benefits: Optional[List[str]] = Field(default_factory=list)
    enhanced_application: Optional[str] = None

    class Config:
        from_attributes = True  # 'orm_mode'가 deprecated 되어 'from_attributes'로 변경