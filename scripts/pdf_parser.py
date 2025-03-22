import os
import re
import pdfplumber
import langchain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
import pinecone
from tqdm import tqdm
import time
import json
import sys
from pathlib import Path

# 상위 디렉토리를 모듈 검색 경로에 추가
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings

# OpenAI 및 Pinecone 초기화
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

pinecone.init(
    api_key=settings.PINECONE_API_KEY,
    environment=settings.PINECONE_ENVIRONMENT
)

# Pinecone 인덱스 생성 또는 가져오기
if settings.PINECONE_INDEX_NAME not in pinecone.list_indexes():
    pinecone.create_index(
        name=settings.PINECONE_INDEX_NAME,
        dimension=1536,  # text-embedding-3-small 모델의 차원
        metric="cosine"
    )

index = pinecone.Index(settings.PINECONE_INDEX_NAME)

def extract_text_from_pdf(pdf_path):
    """PDF에서 텍스트 추출"""
    all_text = ""
    page_texts = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for i, page in enumerate(tqdm(pdf.pages, desc="PDF 페이지 처리 중")):
                text = page.extract_text() or ""
                clean_text = text.replace('\n', ' ').strip()
                
                # 페이지 번호와 함께 저장
                page_texts.append({
                    "page_number": i + 1,
                    "text": clean_text,
                    "total_pages": total_pages
                })
                
                all_text += clean_text + " "
    
        print(f"PDF에서 총 {len(page_texts)} 페이지 추출 완료")
        return all_text, page_texts
    
    except Exception as e:
        print(f"PDF 추출 오류: {e}")
        return "", []

def split_text_into_chunks(text, page_texts):
    """텍스트를 청크로 분할"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len,
    )
    
    chunks = text_splitter.split_text(text)
    
    # 청크에 페이지 번호 할당
    chunk_metadata = []
    current_position = 0
    
    for chunk in chunks:
        chunk_start = text.find(chunk, current_position)
        
        if chunk_start != -1:
            current_position = chunk_start
            
            # 청크가 속한 페이지 찾기
            accumulated_length = 0
            page_number = 1
            
            for page_data in page_texts:
                page_text = page_data["text"]
                page_length = len(page_text)
                
                if accumulated_length + page_length > chunk_start:
                    page_number = page_data["page_number"]
                    break
                
                accumulated_length += page_length + 1  # +1 for space added between pages
            
            chunk_metadata.append({
                "chunk": chunk,
                "page_number": page_number
            })
    
    print(f"텍스트를 {len(chunks)} 청크로 분할 완료")
    return chunk_metadata

def embed_and_store_chunks(chunk_metadata):
    """청크를 임베딩하여 Pinecone에 저장"""
    batch_size = 100  # 한 번에 처리할 청크 수
    vectors = []
    
    for i in tqdm(range(0, len(chunk_metadata), batch_size), desc="청크 임베딩 및 저장 중"):
        # 현재 배치에서 처리할 청크
        current_batch = chunk_metadata[i:i+batch_size]
        chunks = [item["chunk"] for item in current_batch]
        
        # 임베딩 생성
        try:
            embeddings_list = embeddings.embed_documents(chunks)
            
            # 벡터 및 메타데이터 준비
            for j, (chunk_data, embedding) in enumerate(zip(current_batch, embeddings_list)):
                vector_id = f"chunk_{i+j}"
                metadata = {
                    "text": chunk_data["chunk"],
                    "page": chunk_data["page_number"]
                }
                
                vectors.append((vector_id, embedding, metadata))
                
                # 일정 크기의 배치가 모이면 Pinecone에 저장
                if len(vectors) >= 100:
                    upsert_vectors_to_pinecone(vectors)
                    vectors = []  # 벡터 리스트 초기화
        
        except Exception as e:
            print(f"임베딩 오류: {e}")
            continue
    
    # 남은 벡터 저장
    if vectors:
        upsert_vectors_to_pinecone(vectors)
    
    print("모든 청크 임베딩 및 저장 완료")

def upsert_vectors_to_pinecone(vectors):
    """벡터를 Pinecone에 업서트"""
    try:
        pinecone_vectors = [(id, embedding, metadata) for id, embedding, metadata in vectors]
        index.upsert(vectors=pinecone_vectors)
        time.sleep(1)  # API 제한 방지
    except Exception as e:
        print(f"Pinecone 업서트 오류: {e}")

def process_pdf(pdf_path):
    """PDF 처리 전체 파이프라인"""
    print(f"PDF 처리 시작: {pdf_path}")
    
    # 1. PDF에서 텍스트 추출
    all_text, page_texts = extract_text_from_pdf(pdf_path)
    
    if not all_text:
        print("텍스트 추출 실패")
        return False
    
    # 2. 텍스트를 청크로 분할
    chunk_metadata = split_text_into_chunks(all_text, page_texts)
    
    # 3. 청크 임베딩 및 저장
    embed_and_store_chunks(chunk_metadata)
    
    print("PDF 처리 완료")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python pdf_parser.py <PDF 파일 경로>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    process_pdf(pdf_path)