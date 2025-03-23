import os
import re
from tqdm import tqdm
from pinecone import Pinecone
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 가져오기
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "labor-policy")

# 작업 디렉토리 설정
work_dir = "work_labor_sample"
merged_file = os.path.join(work_dir, "labor_sample_text.txt")

# 텍스트 파일 다시 읽기
with open(merged_file, 'r', encoding='utf-8') as f:
    text = f.read()

# 텍스트 청킹 함수 - 페이지 메타데이터 포함
def create_chunks_with_metadata(text, chunk_size=1000, chunk_overlap=200):
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    # 페이지 정보 추출을 위한 준비
    chunks = []
    metadatas = []
    
    # 페이지 구분자로 텍스트 분리
    page_pattern = "\n--- Page (\d+) ---\n"
    page_splits = re.split(page_pattern, text)
    
    # 첫 요소는 빈 문자열일 수 있으므로 제거
    if page_splits[0] == '':
        page_splits = page_splits[1:]
    
    # 페이지 번호와 내용 쌍으로 재구성
    pages = []
    for i in range(0, len(page_splits), 2):
        if i+1 < len(page_splits):
            page_num = page_splits[i]
            content = page_splits[i+1]
            pages.append((page_num, content))
    
    # 텍스트 스플리터 설정
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    # 각 페이지별로 청크 생성 및 메타데이터 추가
    for page_num, content in pages:
        page_chunks = text_splitter.split_text(content)
        for chunk in page_chunks:
            chunks.append(chunk)
            metadatas.append({"page": page_num})
    
    return chunks, metadatas

# 임베딩 생성 함수
def get_embeddings(chunks):
    from openai import OpenAI
    import time
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)
    embeddings = []
    
    for chunk in tqdm(chunks, desc="임베딩 생성 중"):
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        embeddings.append(response.data[0].embedding)
        time.sleep(0.1)  # API 속도 제한 방지
    
    return embeddings

# Pinecone에 업로드 - 메타데이터 포함
def upload_to_pinecone(chunks, embeddings, metadatas):
    print("Pinecone에 업로드 중...")
    
    # Pinecone 초기화
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # 인덱스 존재 확인
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    if INDEX_NAME not in existing_indexes:
        print(f"인덱스 '{INDEX_NAME}' 생성 중...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,  # text-embedding-3-small 차원
            metric="cosine"
        )
    
    # 인덱스 연결
    index = pc.Index(INDEX_NAME)
    
    # 데이터 업로드
    batch_size = 100
    for i in tqdm(range(0, len(chunks), batch_size), desc="벡터 업로드 중"):
        i_end = min(i + batch_size, len(chunks))
        
        vectors = []
        for j in range(i, i_end):
            vectors.append({
                "id": f"chunk_{j}",
                "values": embeddings[j],
                "metadata": {
                    "text": chunks[j],
                    "page": metadatas[j]["page"]
                }
            })
        
        # 벡터 업로드
        index.upsert(vectors=vectors)
    
    print("Pinecone 업로드 완료!")

# 메인 실행 코드
def main():
    print(f"텍스트 파일 '{merged_file}' 처리 중...")
    
    # 텍스트 청킹 (메타데이터 포함)
    chunks, metadatas = create_chunks_with_metadata(text)
    print(f"{len(chunks)}개의 청크 생성 완료")
    
    # 임베딩 생성
    embeddings = get_embeddings(chunks)
    
    # Pinecone에 업로드 (메타데이터 포함)
    upload_to_pinecone(chunks, embeddings, metadatas)

if __name__ == "__main__":
    main()