import os
import argparse
import requests
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Upstage OCR API 키 가져오기
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
UPSTAGE_API_URL = os.getenv("UPSTAGE_API_URL", "https://api.upstage.ai/v1/ocr")

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
        'Authorization': f'Bearer {UPSTAGE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    for page_num in tqdm(range(1, num_pages + 1), desc="Processing pages"):
        image_path = os.path.join(image_folder, f"page_{page_num}.png")
        output_file = os.path.join(output_folder, f"page_{page_num}.txt")
        
        # 이미지 파일을 base64로 인코딩
        import base64
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # API 요청 데이터 준비
        payload = {
            "image": encoded_image,
            "language": "ko",  # 한국어 설정
            "detect_orientation": True
        }
        
        # OCR API 호출
        try:
            response = requests.post(UPSTAGE_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # 결과에서 텍스트 추출
            if 'text' in result:
                detected_text = result['text']
            else:
                detected_text = ""
                # 상세 결과가 있는 경우 (예: 각 텍스트 블록별 정보)
                if 'results' in result:
                    for block in result['results']:
                        if 'text' in block:
                            detected_text += block['text'] + "\n"
            
            # 결과를 텍스트 파일로 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(detected_text)
            
            # API 속도 제한 방지
            time.sleep(0.5)
        
        except Exception as e:
            print(f"Error on page {page_num}: {str(e)}")
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
    parser = argparse.ArgumentParser(description="Process PDF with Upstage OCR")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()
    
    # 작업 폴더 설정
    base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    work_dir = f"work_{base_name}_upstage"
    images_folder = os.path.join(work_dir, "images")
    ocr_folder = os.path.join(work_dir, "ocr")
    merged_file = os.path.join(work_dir, f"{base_name}_text.txt")
    
    # 작업 폴더 생성
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. PDF를 이미지로 변환
    print("Converting PDF to images...")
    num_pages = convert_pdf_to_images(args.pdf_path, images_folder)
    
    # 2. OCR 수행
    print("Performing Upstage OCR on images...")
    perform_ocr_on_images(images_folder, ocr_folder, num_pages)
    
    # 3. 텍스트 파일 병합
    print("Merging text files...")
    merge_text_files(ocr_folder, merged_file, num_pages)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main()