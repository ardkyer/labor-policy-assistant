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
MAX_RETRIES = 3  # API 호출 실패 시 최대 재시도 횟수

def convert_pdf_to_images(pdf_path, output_folder, start_page, end_page, crop_right=True):
    import fitz  # PyMuPDF
    
    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # PDF 문서 열기
    doc = fitz.open(pdf_path)
    
    # 페이지 범위 확인 및 조정
    total_pages = len(doc)
    if start_page > total_pages:
        print(f"시작 페이지({start_page})가 총 페이지 수({total_pages})를 초과합니다.")
        return 0
    
    if end_page > total_pages:
        print(f"종료 페이지({end_page})가 총 페이지 수({total_pages})를 초과합니다. {total_pages}로 조정합니다.")
        end_page = total_pages
    
    # 지정된 페이지 범위만 이미지로 변환
    for page_idx in range(start_page - 1, end_page):
        page = doc.load_page(page_idx)
        
        # 페이지 크기 가져오기
        rect = page.rect
        
        if crop_right:
            # 오른쪽 20%를 자르기 위한 새 직사각형 생성 (왼쪽 80%만 사용)
            crop_rect = fitz.Rect(rect.x0, rect.y0, rect.x1 * 0.9, rect.y1)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72), clip=crop_rect)
        else:
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
        output_file = os.path.join(output_folder, f"page_{page_idx + 1}.png")
        pix.save(output_file)
    
    return end_page - start_page + 1  # 처리된 페이지 수 반환

def perform_ocr_on_image(image_path, output_file, headers, retry_count=0):
    """단일 이미지에 대한 OCR 수행 함수 (재시도 로직 포함)"""
    
    # 이미지 파일 읽기
    with open(image_path, "rb") as f:
        file_data = f.read()
    
    # API 요청 데이터 준비
    request_json = {
        'images': [
            {
                'format': 'png',
                'name': os.path.basename(image_path).split('.')[0]
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
        
        return True
    
    except Exception as e:
        print(f"Error on {os.path.basename(image_path)}: {str(e)}")
        # 상세 오류 정보 출력
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        
        # 최대 재시도 횟수에 도달하지 않았다면 재시도
        if retry_count < MAX_RETRIES:
            print(f"Retrying {os.path.basename(image_path)} (Attempt {retry_count + 2}/{MAX_RETRIES + 1})")
            time.sleep(2)  # 재시도 간격 조절
            return perform_ocr_on_image(image_path, output_file, headers, retry_count + 1)
        
        # 최대 재시도 횟수에 도달했다면 빈 파일 생성
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        return False

def perform_ocr_on_images(image_folder, ocr_folder, start_page, end_page):
    """지정된 페이지 범위에 대해 OCR 수행"""
    
    # 출력 폴더가 없으면 생성
    if not os.path.exists(ocr_folder):
        os.makedirs(ocr_folder)
    
    # API 헤더 설정
    headers = {
        'X-OCR-SECRET': NAVER_OCR_SECRET_KEY
    }
    
    # 지정된 페이지 범위에 대해 OCR 수행
    for page_num in tqdm(range(start_page, end_page + 1), desc="OCR 처리 중"):
        image_path = os.path.join(image_folder, f"page_{page_num}.png")
        output_file = os.path.join(ocr_folder, f"page_{page_num}.txt")
        
        if os.path.exists(image_path):
            success = perform_ocr_on_image(image_path, output_file, headers)
            # API 호출 간격 조절
            time.sleep(0.5)
        else:
            print(f"이미지 파일이 없습니다: {image_path}")

def merge_text_files(ocr_folder, merged_file, start_page, end_page):
    """지정된 페이지 범위의 텍스트 파일 병합"""
    
    with open(merged_file, 'w', encoding='utf-8') as outfile:
        for page_num in range(start_page, end_page + 1):
            text_file = os.path.join(ocr_folder, f"page_{page_num}.txt")
            
            if os.path.exists(text_file):
                with open(text_file, 'r', encoding='utf-8') as infile:
                    outfile.write(f"\n--- Page {page_num} ---\n\n")
                    outfile.write(infile.read())
            else:
                outfile.write(f"\n--- Page {page_num} --- (처리 실패)\n\n")

def main():
    parser = argparse.ArgumentParser(description="특정 페이지 범위만 Naver CLOVA OCR로 처리")
    parser.add_argument("--start", type=int, default=1, help="시작 페이지 번호 (기본값: 1)")
    parser.add_argument("--end", type=int, default=10, help="종료 페이지 번호 (기본값: 10)")
    parser.add_argument("--pdf", type=str, help="PDF 파일 경로 (기본값: labor.pdf)")
    args = parser.parse_args()
    
    # PDF 경로 설정
    if args.pdf:
        # 사용자가 지정한 경로 사용
        pdf_path = args.pdf
    else:
        # 기본 경로 시도 (여러 가능한 위치)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_paths = [
            os.path.join(base_dir, "data", "policies", "labor.pdf"),  # 프로젝트 구조 기준
            "data/policies/labor.pdf",                                # 현재 디렉토리 기준
            "../data/policies/labor.pdf",                             # scripts 폴더에서 실행 시
            "labor.pdf"                                               # 같은 디렉토리
        ]
        
        pdf_path = None
        for path in possible_paths:
            if os.path.exists(path):
                pdf_path = path
                break
        
        if pdf_path is None:
            print("오류: labor.pdf 파일을 찾을 수 없습니다.")
            print("현재 작업 디렉토리:", os.getcwd())
            print("--pdf 옵션으로 정확한 경로를 지정해주세요.")
            return
    
    # 시작 및 종료 페이지
    start_page = args.start
    end_page = args.end
    
    print(f"처리할 페이지 범위: {start_page}~{end_page}")
    
    # 작업 폴더 설정 (페이지 범위 포함)
    work_dir = f"work_labor_naver_{start_page}~{end_page}"
    images_folder = os.path.join(work_dir, "images")
    ocr_folder = os.path.join(work_dir, "ocr")
    merged_file = os.path.join(work_dir, f"labor_{start_page}~{end_page}_text.txt")
    
    # 작업 폴더 생성
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. PDF를 이미지로 변환 (지정된 페이지만)
    print(f"PDF {start_page}~{end_page} 페이지를 이미지로 변환 중...")
    processed_pages = convert_pdf_to_images(pdf_path, images_folder, start_page, end_page)
    
    if processed_pages > 0:
        print(f"{processed_pages}페이지 변환 완료")
        
        # 2. OCR 수행
        print("Naver CLOVA OCR 처리 중...")
        perform_ocr_on_images(images_folder, ocr_folder, start_page, end_page)
        
        # 3. 텍스트 파일 병합
        print("텍스트 파일 병합 중...")
        merge_text_files(ocr_folder, merged_file, start_page, end_page)
        
        print(f"처리 완료! 결과는 {merged_file}에 저장되었습니다.")
    else:
        print("처리할 페이지가 없습니다.")

if __name__ == "__main__":
    main()