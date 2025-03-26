import os
import argparse
from tqdm import tqdm
import pytesseract
from PIL import Image
import cv2
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

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
    
    for page_num in tqdm(range(1, num_pages + 1), desc="Processing pages"):
        image_path = os.path.join(image_folder, f"page_{page_num}.png")
        output_file = os.path.join(output_folder, f"page_{page_num}.txt")
        
        # 이미지 전처리
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 노이즈 제거 및 선명도 향상
        gray = cv2.medianBlur(gray, 3)
        # 대비 향상
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # OCR 실행
        custom_config = r'--oem 3 --psm 6 -l kor+eng'
        text = pytesseract.image_to_string(gray, config=custom_config)
        
        # 결과를 텍스트 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)

def merge_text_files(text_folder, output_file, num_pages):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for page_num in range(1, num_pages + 1):
            text_file = os.path.join(text_folder, f"page_{page_num}.txt")
            
            if os.path.exists(text_file):
                with open(text_file, 'r', encoding='utf-8') as infile:
                    outfile.write(f"\n--- Page {page_num} ---\n\n")
                    outfile.write(infile.read())

def main():
    parser = argparse.ArgumentParser(description="Process PDF with Tesseract OCR")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    args = parser.parse_args()
    
    # 작업 폴더 설정
    base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    work_dir = f"work_{base_name}_tesseract"
    images_folder = os.path.join(work_dir, "images")
    ocr_folder = os.path.join(work_dir, "ocr")
    merged_file = os.path.join(work_dir, f"{base_name}_text.txt")
    
    # 작업 폴더 생성
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. PDF를 이미지로 변환
    print("Converting PDF to images...")
    num_pages = convert_pdf_to_images(args.pdf_path, images_folder)
    
    # 2. OCR 수행
    print("Performing Tesseract OCR on images...")
    perform_ocr_on_images(images_folder, ocr_folder, num_pages)
    
    # 3. 텍스트 파일 병합
    print("Merging text files...")
    merge_text_files(ocr_folder, merged_file, num_pages)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main()