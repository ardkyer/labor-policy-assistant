import os
import sys
from pathlib import Path
import json
import pinecone
from tqdm import tqdm
import time
from sqlalchemy.orm import Session

# 상위 디렉토리를 모듈 검색 경로에 추가
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings
from backend.app.db.base import engine, SessionLocal, Base
from backend.app.db.models import PolicyChunk, Policy

def create_tables():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블 생성 완료")

def store_chunks_in_db(index_name):
    """Pinecone의 청크를 데이터베이스에 저장"""
    try:
        pinecone.init(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT
        )
        
        if index_name not in pinecone.list_indexes():
            print(f"인덱스 '{index_name}'를 찾을 수 없습니다.")
            return False
        
        index = pinecone.Index(index_name)
        
        # 인덱스 상태 확인
        index_stats = index.describe_index_stats()
        total_vectors = index_stats['total_vector_count']
        
        print(f"인덱스 '{index_name}'에서 {total_vectors}개의 벡터를 가져옵니다.")
        
        # 데이터베이스 세션 생성
        db = SessionLocal()
        
        # 청크 ID 배치 생성
        batch_size = 100
        fetch_ids = []
        
        for i in range(0, total_vectors, batch_size):
            fetch_ids.append(i)
        
        # 각 배치 처리
        for batch_id in tqdm(range(0, len(fetch_ids)), desc="청크 데이터베이스 저장 중"):
            try:
                # 벡터 ID 패턴
                vector_ids = [f"chunk_{fetch_ids[batch_id] + j}" for j in range(batch_size) if fetch_ids[batch_id] + j < total_vectors]
                
                # Pinecone에서 메타데이터 가져오기
                fetch_response = index.fetch(ids=vector_ids)
                
                # 데이터베이스에 저장
                for vector_id, vector_data in fetch_response['vectors'].items():
                    metadata = vector_data['metadata']
                    
                    # PolicyChunk 객체 생성
                    policy_chunk = PolicyChunk(
                        content=metadata.get('text', ''),
                        page_number=metadata.get('page', None),
                        vector_id=vector_id,
                        metadata=metadata
                    )
                    
                    db.add(policy_chunk)
                
                db.commit()
                time.sleep(0.5)  # API 제한 방지
                
            except Exception as e:
                db.rollback()
                print(f"배치 {batch_id} 처리 오류: {e}")
                continue
        
        db.close()
        print("청크 데이터베이스 저장 완료")
        return True
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

def extract_policies_from_chunks():
    """청크에서 정책 정보 추출 및 저장"""
    db = SessionLocal()
    
    try:
        # 모든 청크 가져오기
        chunks = db.query(PolicyChunk).all()
        print(f"총 {len(chunks)}개의 청크에서 정책 추출 시작")
        
        # 간단한 휴리스틱 기반 정책 추출
        # 실제 구현에서는 LLM을 활용하여 구조화된 정보 추출이 필요
        current_policy = None
        current_page = None
        
        for chunk in tqdm(chunks, desc="정책 추출 중"):
            text = chunk.content
            page = chunk.page_number
            
            # 새로운 페이지나 새로운 정책 제목을 만나면 정책 객체 생성
            if page != current_page or '지원대상' in text or '지원내용' in text:
                # 정책 제목으로 보이는 텍스트 탐색
                title_match = re.search(r'([0-9]+\.\s.+?)(\n|$)', text)
                
                if title_match:
                    title = title_match.group(1).strip()
                    
                    # 새 정책 객체 생성
                    current_policy = Policy(
                        title=title,
                        description=text,
                        source_page=page
                    )
                    
                    db.add(current_policy)
                    db.flush()  # ID 생성을 위한 플러시
                    
                    # 청크와 정책 연결
                    chunk.policy_id = current_policy.id
                    
                    current_page = page
            
            elif current_policy:
                # 현재 정책 설명 업데이트
                current_policy.description += " " + text
                
                # 청크와 정책 연결
                chunk.policy_id = current_policy.id
        
        db.commit()
        print("정책 추출 및 저장 완료")
        
    except Exception as e:
        db.rollback()
        print(f"정책 추출 오류: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    # 데이터베이스 테이블 생성
    create_tables()
    
    # Pinecone에서 청크 가져와 DB 저장
    store_chunks_in_db(settings.PINECONE_INDEX_NAME)
    
    # 청크에서 정책 정보 추출
    extract_policies_from_chunks()