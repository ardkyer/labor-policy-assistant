import os
import argparse
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
import time
from openai import OpenAI
from dotenv import load_dotenv
import pinecone

# .env 파일 로드
load_dotenv()

# 환경 변수에서 설정 불러오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "labor-policy")

def convert_pdf_to_images(pdf_path, output_folder):
    import fitz  # PyMuPDF
    import os
    
    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # PDF 문서 열기
    doc = fitz.open(pdf_path)
    
    # 각 페이지를 이미지로 변환
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI로 렌더링
        output_file = os.path.join(output_folder, f"page_{page_num+1}.png")
        pix.save(output_file)
    
    return len(doc)

def perform_ocr_on_images(image_folder, output_folder, num_pages):
    import easyocr
    import os
    
    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # EasyOCR 리더 초기화 (한국어 + 영어)
    reader = easyocr.Reader(['ko', 'en'])
    
    for page_num in range(1, num_pages + 1):
        image_path = os.path.join(image_folder, f"page_{page_num}.png")
        output_file = os.path.join(output_folder, f"page_{page_num}.txt")
        
        # OCR 실행
        results = reader.readtext(image_path)
        
        # 결과를 텍스트 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            for (_, text, _) in results:
                f.write(text + '\n')
        
        print(f"Processed page {page_num}/{num_pages}")

def merge_text_files(text_folder, output_file, num_pages):
    import os
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for page_num in range(1, num_pages + 1):
            text_file = os.path.join(text_folder, f"page_{page_num}.txt")
            
            if os.path.exists(text_file):
                with open(text_file, 'r', encoding='utf-8') as infile:
                    outfile.write(f"\n--- Page {page_num} ---\n\n")
                    outfile.write(infile.read())

def create_chunks(text_file, chunk_size=1000, chunk_overlap=200):
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_text(text)
    return chunks

def get_embeddings(chunks):
    client = OpenAI(api_key=OPENAI_API_KEY)
    embeddings = []
    
    for chunk in tqdm(chunks):
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        embeddings.append(response.data[0].embedding)
        time.sleep(0.1)  # API 속도 제한 방지
    
    return embeddings

def upload_to_pinecone(chunks, embeddings):
    # 최신 버전 Pinecone API 사용
    from pinecone import Pinecone
    
    # Pinecone 초기화
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # 인덱스 목록 확인
    indexes = [index.name for index in pc.list_indexes()]
    
    # 인덱스가 존재하지 않으면 생성
    if INDEX_NAME not in indexes:
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,  # text-embedding-3-small 차원
            metric="cosine",
        )
    
    # 인덱스 연결
    index = pc.Index(INDEX_NAME)
    
    # 데이터 업로드
    batch_size = 100
    for i in tqdm(range(0, len(chunks), batch_size)):
        i_end = min(i + batch_size, len(chunks))
        
        vectors = []
        for j in range(i, i_end):
            vectors.append({
                "id": f"chunk_{j}",
                "values": embeddings[j],
                "metadata": {"text": chunks[j]}
            })
        
        # 벡터 업로드
        index.upsert(vectors=vectors)

def main():
    parser = argparse.ArgumentParser(description="Process PDF with OCR and upload to Pinecone")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()
    
    # 작업 폴더 설정
    base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    work_dir = f"work_{base_name}"
    images_folder = os.path.join(work_dir, "images")
    ocr_folder = os.path.join(work_dir, "ocr")
    merged_file = os.path.join(work_dir, f"{base_name}_text.txt")
    
    # 작업 폴더 생성
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. PDF를 이미지로 변환
    print("Converting PDF to images...")
    num_pages = convert_pdf_to_images(args.pdf_path, images_folder)
    
    # 2. OCR 수행
    print("Performing OCR on images...")
    perform_ocr_on_images(images_folder, ocr_folder, num_pages)
    
    # 3. 텍스트 파일 병합
    print("Merging text files...")
    merge_text_files(ocr_folder, merged_file, num_pages)
    
    # 4. 청크 생성
    print("Creating text chunks...")
    chunks = create_chunks(merged_file)
    print(f"Created {len(chunks)} chunks")
    
    # 5. 임베딩 생성
    print("Generating embeddings...")
    embeddings = get_embeddings(chunks)
    
    # 6. Pinecone에 업로드
    print("Uploading to Pinecone...")
    upload_to_pinecone(chunks, embeddings)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main()