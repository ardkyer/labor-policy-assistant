import os
import json
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # 프로젝트 기본 설정
    PROJECT_NAME: str = "고용노동부 정책 지원 어시스턴트"
    API_V1_STR: str = "/api/v1"
    
    # CORS 설정 (배포 환경 포함하도록 수정됨)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8000", 
        "https://labor-policy-assistant.vercel.app",  # Vercel 배포 도메인
        "https://labor-policy-assistant-git-main.vercel.app",  # Vercel 프리뷰 도메인 (Git 브랜치용)
        "https://*.vercel.app"  # 모든 Vercel 서브도메인 허용
    ]
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",")]
        return v
    
    # 데이터베이스 설정
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "labor_policy")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    # JWT 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일
    
    # OpenAI API 설정
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Pinecone 설정
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "labor-policy")
    
    # PDF 설정
    PDF_STORAGE_PATH: str = os.getenv("PDF_STORAGE_PATH", "data/policies")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()