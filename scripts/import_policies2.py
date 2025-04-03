# scripts/import_policies_by_policy_unit.py
import re
import os
import mysql.connector
from datetime import datetime

# OCR 텍스트 파일 읽기
ocr_file_path = "work_labor_naver_21~30/labor_21~30_text.txt"  # 경로 수정
try:
    with open(ocr_file_path, "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {ocr_file_path}")
    exit(1)

# 디버깅: 파일 내용 확인
print(f"파일 내용 일부: {content[:300]}...")

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
print(f"총 페이지 수: {len(pages)}")

# 정책별로 내용을 추출하는 함수
def extract_policies_from_pages(pages):
    policies = []
    current_policy = None
    current_policy_content = ""
    current_page = 0
    
    # 정책 시작 패턴: 숫자 + 정책명
    policy_pattern = re.compile(r'^(\d+)\s+([가-힣\s]+(?:사업|지원|운영|제도|센터|병행|프로젝트|플러스센터))', re.MULTILINE)
    
    for page_idx, page_content in enumerate(pages):
        page_num = page_idx + 1
        print(f"페이지 {page_num} 분석 중...")
        
        # 현재 페이지에서 정책 시작점 찾기
        policy_matches = list(policy_pattern.finditer(page_content))
        
        if policy_matches:  # 현재 페이지에 정책 시작점이 있는 경우
            for match_idx, match in enumerate(policy_matches):
                policy_id = match.group(1).strip()
                policy_title = match.group(2).strip()
                
                # 이전 정책 저장 (첫 정책 제외)
                if current_policy is not None:
                    # 현재 매치 위치 이전까지의 내용을 이전 정책에 추가
                    additional_content = page_content[:match.start()]
                    current_policy_content += "\n" + additional_content
                    
                    # 이전 정책 정보 파싱 및 저장
                    policy_data = parse_policy_data(current_policy, current_policy_content, current_page)
                    policies.append(policy_data)
                
                # 새 정책 시작
                current_policy = {
                    "id": policy_id,
                    "title": policy_title
                }
                current_page = page_num
                
                # 현재 매치 위치부터 다음 매치 또는 페이지 끝까지의 내용을 새 정책에 추가
                if match_idx < len(policy_matches) - 1:
                    next_match = policy_matches[match_idx + 1]
                    current_policy_content = page_content[match.start():next_match.start()]
                else:
                    current_policy_content = page_content[match.start():]
        
        else:  # 현재 페이지에 정책 시작점이 없는 경우 (이어지는 내용)
            if current_policy is not None:
                # 현재 페이지 내용을 현재 정책에 추가
                current_policy_content += "\n" + page_content
    
    # 마지막 정책 저장
    if current_policy is not None:
        policy_data = parse_policy_data(current_policy, current_policy_content, current_page)
        policies.append(policy_data)
    
    return policies

# 정책 내용을 파싱하여 구조화된 데이터로 변환하는 함수
def parse_policy_data(policy, content, page_num):
    policy_id = policy["id"]
    title = policy["title"]
    
    # 부서 정보 추출
    department = ""
    dept_match = re.search(r'고용노동부\s+([가-힣]+과(?:\([가-힣A-Za-z0-9\-]+\))?)', content)
    if dept_match:
        department = dept_match.group(0).strip()
    
    # 사업 목적 추출
    purpose = ""
    purpose_match = re.search(r'사업\s*목적.*?\n●?\s*(.*?)(?=\n\s*사업|\n\s*\(지원|\Z)', content, re.DOTALL)
    if purpose_match:
        purpose = purpose_match.group(1).strip()
    
    # 지원대상 추출
    target = ""
    target_match = re.search(r'\(지원대상\)(.*?)(?=\n\s*\(|\Z)', content, re.DOTALL)
    if target_match:
        target = target_match.group(1).strip()
    
    # 지원내용 추출
    benefits = ""
    benefits_match = re.search(r'\(지원내용\)(.*?)(?=\n\s*\(|\Z)', content, re.DOTALL)
    if benefits_match:
        benefits = benefits_match.group(1).strip()
    
    # 지원조건 추출
    eligibility = ""
    eligibility_match = re.search(r'\(지원조건\)(.*?)(?=\n\s*\(|\Z)', content, re.DOTALL)
    if eligibility_match:
        eligibility = eligibility_match.group(1).strip()
    
    # 지원절차 추출
    process = ""
    process_match = re.search(r'\(지원절차\)(.*?)(?=\n\s*\(|\Z)', content, re.DOTALL)
    if process_match:
        process = process_match.group(1).strip()
    
    # 설명 구성
    description = ""
    if purpose:
        description += f"사업 목적: {purpose}\n\n"
    if target:
        description += f"지원대상: {target}\n\n"
    if benefits:
        description += f"지원내용: {benefits}\n\n"
    if eligibility:
        description += f"지원조건: {eligibility}\n\n"
    if process:
        description += f"지원절차: {process}\n\n"
    
    # 설명이 부족한 경우
    if len(description.strip()) < 100:
        # 일부 내용 사용 (너무 길지 않게)
        description = f"정책 ID {policy_id}: {title}\n\n{content[:800]}..."
    
    # 카테고리 추정
    category = "기타"
    if "청년" in title or "청년" in description:
        category = "청년"
    elif "고령자" in title or "신중년" in title or "중장년" in title:
        category = "고령자"
    elif "장애인" in title:
        category = "장애인"
    elif "여성" in title or "육아" in title or "출산" in title:
        category = "여성/육아"
    elif "외국인" in title:
        category = "외국인"
    
    # 타겟 추정
    target_age_min = None
    target_age_max = None
    target_gender = "ALL"
    
    # 연령 정보 추출
    if "청년" in title or "청년" in description:
        target_age_min = 15
        target_age_max = 34
        
        # 더 구체적인 연령 정보 추출
        age_match = re.search(r'(\d+)세\s*[~-]\s*(\d+)세', content)
        if age_match:
            target_age_min = int(age_match.group(1))
            target_age_max = int(age_match.group(2))
    
    return {
        "policy_id": policy_id,
        "title": title,
        "description": description,
        "category": category,
        "target_age_min": target_age_min,
        "target_age_max": target_age_max,
        "target_gender": target_gender,
        "source_page": page_num,
        "eligibility": eligibility,
        "benefits": benefits,
        "application_process": process,
        "department": department
    }

# 정책 추출
policies = extract_policies_from_pages(pages)
print(f"총 파싱된 정책 수: {len(policies)}")

# 정책 정보 출력
for i, policy in enumerate(policies[:5]):  # 첫 5개 정책 출력
    print(f"\n정책 {i+1}:")
    print(f"ID: {policy['policy_id']}, 제목: {policy['title']}, 페이지: {policy['source_page']}")
    print(f"카테고리: {policy['category']}")
    print(f"부서: {policy.get('department', '')}")
    print(f"내용 일부: {policy['description'][:100]}...")

# 정책 정보 데이터베이스에 저장
insert_count = 0
for policy in policies:
    # 현재 시간
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # SQL 쿼리 작성
    sql = """
    INSERT INTO policies 
    (title, description, category, target_age_min, target_age_max, target_gender, source_page, 
    eligibility, benefits, application_process, created_at, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        policy["title"],
        policy["description"],
        policy["category"],
        policy["target_age_min"],
        policy["target_age_max"],
        policy["target_gender"],
        policy["source_page"],
        policy["eligibility"],
        policy["benefits"],
        policy["application_process"],
        now,
        now
    )
    
    try:
        cursor.execute(sql, values)
        insert_count += 1
    except mysql.connector.Error as err:
        print(f"삽입 오류 (정책 ID {policy['policy_id']}): {err}")

# 변경사항 저장
connection.commit()
print(f"정책 데이터 {insert_count}개를 MySQL에 저장했습니다.")

# 연결 종료
cursor.close()
connection.close()