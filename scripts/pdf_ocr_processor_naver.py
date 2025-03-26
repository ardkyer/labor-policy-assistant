import os
import argparse
import requests
import time
import json
import uuid
from tqdm import tqdm
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Naver CLOVA OCR API 키 가져오기
NAVER_OCR_SECRET_KEY = os.getenv("NAVER_CLOVA_SECRET_KEY")
NAVER_OCR_API_URL = os.getenv("NAVER_CLOVA_API_URL")

def convert_pdf_to_images(pdf_path, output_folder):
    import fitz  # PyMuPDF
    
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
    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # API 헤더 설정
    headers = {
        'X-OCR-SECRET': NAVER_OCR_SECRET_KEY
    }
    
    for page_num in tqdm(range(1, num_pages + 1), desc="Processing pages"):
        image_path = os.path.join(image_folder, f"page_{page_num}.png")
        output_file = os.path.join(output_folder, f"page_{page_num}.txt")
        
        # 이미지 파일 읽기
        with open(image_path, "rb") as f:
            file_data = f.read()
        
        # API 요청 데이터 준비
        request_json = {
            'images': [
                {
                    'format': 'png',
                    'name': f'page_{page_num}'
                }
            ],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(time.time() * 1000)
        }
        
        # 멀티파트 폼 데이터 준비
        files = [
            ('file', ('image.png', file_data, 'image/png'))
        ]
        
        # OCR API 호출
        try:
            # data 부분에 JSON 문자열을, files 부분에 이미지 파일을 전송
            response = requests.post(
                NAVER_OCR_API_URL, 
                headers=headers, 
                data={'message': json.dumps(request_json)},
                files=files
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 디버깅용 결과 출력
            if page_num == 1:
                print("API 응답 형식:", json.dumps(result, indent=2)[:500] + "...")
            
            # 결과에서 텍스트 추출
            full_text = ""
            if 'images' in result and len(result['images']) > 0:
                for field in result['images'][0].get('fields', []):
                    if 'inferText' in field:
                        full_text += field['inferText'] + ' '
                        if field.get('lineBreak', False):
                            full_text += '\n'
                    
                # 필드 구조가 다른 경우를 위한 대체 처리
                if not full_text and 'text' in result['images'][0]:
                    full_text = result['images'][0]['text']
            
            # 결과를 텍스트 파일로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # API 호출 간격 조절
            time.sleep(0.5)
        
        except Exception as e:
            print(f"Error on page {page_num}: {str(e)}")
            # 상세 오류 정보 출력
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
                
            # 에러 발생 시 빈 파일 생성
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("")

def merge_text_files(text_folder, output_file, num_pages):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for page_num in range(1, num_pages + 1):
            text_file = os.path.join(text_folder, f"page_{page_num}.txt")
            
            if os.path.exists(text_file):
                with open(text_file, 'r', encoding='utf-8') as infile:
                    outfile.write(f"\n--- Page {page_num} ---\n\n")
                    outfile.write(infile.read())

def main():
    parser = argparse.ArgumentParser(description="Process PDF with Naver CLOVA OCR")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()
    
    # 작업 폴더 설정
    base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    work_dir = f"work_{base_name}_naver"
    images_folder = os.path.join(work_dir, "images")
    ocr_folder = os.path.join(work_dir, "ocr")
    merged_file = os.path.join(work_dir, f"{base_name}_text.txt")
    
    # 작업 폴더 생성
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. PDF를 이미지로 변환
    print("Converting PDF to images...")
    num_pages = convert_pdf_to_images(args.pdf_path, images_folder)
    
    # 2. OCR 수행
    print("Performing Naver CLOVA OCR on images...")
    perform_ocr_on_images(images_folder, ocr_folder, num_pages)
    
    # 3. 텍스트 파일 병합
    print("Merging text files...")
    merge_text_files(ocr_folder, merged_file, num_pages)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main()