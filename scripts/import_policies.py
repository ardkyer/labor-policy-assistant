# scripts/import_policies.py
import re
import os
import mysql.connector

# OCR 텍스트 파일 읽기
# ocr_file_path = "work_labor_sample_naver/labor_sample_text.txt"
ocr_file_path = "work_labor_naver_23~23/labor_23~23_text.txt"

try:
    with open(ocr_file_path, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {ocr_file_path}")
    exit(1)

# MySQL 연결 설정
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "password",
    "database": "labor_policy",
    "port": 3306
}

# 데이터베이스 연결
try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    print("MySQL 데이터베이스에 연결되었습니다.")
except mysql.connector.Error as err:
    print(f"MySQL 연결 오류: {err}")
    exit(1)

# 테이블 구조 확인
try:
    cursor.execute("DESCRIBE policies")
    columns = cursor.fetchall()
    print("테이블 구조:")
    for column in columns:
        print(column)
except mysql.connector.Error as err:
    print(f"테이블 구조 조회 오류: {err}")

# 페이지별로 분리
pages = content.split("--- Page ")
pages = [page.strip() for page in pages if page.strip()]

# 정책 목록 파싱 (목차에서)
policy_titles = {}
contents_pattern = re.compile(r"\((\d+)\) (.+?) (\d+)")
for page in pages:
    matches = contents_pattern.findall(page)
    for match in matches:
        policy_id, title, page_num = match
        policy_titles[policy_id] = {"title": title, "page": int(page_num)}

# 각 정책 상세 내용 파싱 및 저장
insert_count = 0
for policy_id, policy_info in policy_titles.items():
    title = policy_info["title"]
    page_num = policy_info["page"]
    
    # 해당 페이지 내용 가져오기
    page_content = ""
    for page in pages:
        if page.startswith(f"{page_num} ---"):
            page_content = page
            break
    
    # 카테고리 추정
    category = "기타"
    if "청년" in title:
        category = "청년"
    elif "고령자" in title or "신중년" in title:
        category = "고령자"
    elif "장애인" in title:
        category = "장애인"
    elif "여성" in title or "육아" in title:
        category = "여성/육아"
    elif "외국인" in title:
        category = "외국인"
    
    # 타겟 추정
    target_age_min = None
    target_age_max = None
    target_gender = "ALL"
    
    if "청년" in title:
        target_age_min = 18
        target_age_max = 34
    elif "고령자" in title or "신중년" in title:
        target_age_min = 50
        
    if "여성" in title:
        target_gender = "F"
    
    # SQL 쿼리 작성
    description = f"정책 ID {policy_id}: {title}에 대한 설명입니다."
    
    sql = """
    INSERT INTO policies (title, description, category, target_age_min, target_age_max, target_gender, source_page)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        title,
        description,
        category,
        target_age_min,
        target_age_max,
        target_gender,
        page_num
    )
    
    try:
        cursor.execute(sql, values)
        insert_count += 1
    except mysql.connector.Error as err:
        print(f"삽입 오류 (정책 ID {policy_id}): {err}")

# 변경사항 저장
connection.commit()
print(f"정책 데이터 {insert_count}개를 MySQL에 저장했습니다.")

# 연결 종료
cursor.close()
connection.close()