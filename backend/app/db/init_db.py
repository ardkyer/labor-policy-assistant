# app/db/init_db.py 파일 생성
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.models import User, Policy, PolicyChunk  # 모든 모델 임포트

# 데이터베이스 엔진 생성
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

# 데이터베이스 테이블 생성
def init_db():
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블이 생성되었습니다.")

if __name__ == "__main__":
    init_db()