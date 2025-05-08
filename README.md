<div align="center">
  <br>
  <img width="300" src="./frontend/public/assets/images/logo.png">

  <h2>AI로 더 쉽게 찾는 고용노동정책, Labor Policy AI Assistant</h2></hr>
  고용노동부의 방대한 정책 정보를 시민들이 더 쉽게 접근하고 활용할 수 있도록 돕는 AI 기반 서비스입니다.
  <h3><a href="https://labor-policy-assistant.vercel.app"> 🔍 직접 사용해보기 📋</a></h3>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white" alt="Python badge">
    <img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=React&logoColor=black" alt="React badge">
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=FastAPI&logoColor=white" alt="FastAPI badge">
    <img src="https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=MySQL&logoColor=white" alt="MySQL badge">
    <img src="https://img.shields.io/badge/Pinecone-111111?style=flat-square&logoColor="white alt="Pinecone badge">
    <img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=OpenAI&logoColor=white" alt="OpenAI badge">
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white" alt="Tailwind CSS badge">
  </p>
</div>
<br>

## 📑 목차
1. [프로젝트 소개](#-프로젝트-소개)
2. [기능 소개](#-기능-소개)
3. [아키텍처](#-아키텍처)
4. [데이터 파이프라인](#-데이터-파이프라인)
5. [설치 및 실행](#-설치-및-실행)
6. [API 목록](#-api-목록)
7. [폴더 구조](#-폴더-구조)
8. [MySQL DB 구조](#-mysql-db-구조)
9. [향후 계획](#-향후-계획)
10. [개발자 정보](#-개발자-정보)

## 🚀 프로젝트 소개
Labor Policy AI Assistant는 고용노동부의 방대한 정책 정보를 쉽게 찾고 활용할 수 있도록 돕는 **AI 기반 정책 추천 및 상담 서비스**입니다.  
이 프로젝트는 **제4회 고용노동 공공데이터 활용 공모전**에 제출되었으며, 319페이지에 달하는 '한권으로 통하는 고용노동정책' PDF 자료를 AI 기술로 분석하여 개인 맞춤형 서비스를 제공합니다.

🔹 **AI 기반 정책 매칭**: 사용자의 프로필(나이, 성별, 취업 상태 등)을 기반으로 적합한 정책 추천  
🔹 **LLM 기반 질의응답**: 고용노동 정책에 관한 자유로운 질의응답 서비스  

## 🏗️ 기능 소개

### 🔑 회원가입 및 로그인
- 사용자 프로필 기반 맞춤형 서비스 제공을 위한 회원 관리 시스템
- 나이, 성별, 취업 상태 등 정책 추천에 필요한 프로필 정보 입력

![회원가입 화면](./docs/imgs/signup.png)

### 🔍 맞춤형 정책 추천
- 사용자 프로필에 기반한 개인화된 정책 추천
- 추천 정책의 요약 정보 및 원문 PDF 다운로드 제공

![정책추천 화면](./docs/imgs/policy_recommendation.png)

### 💬 AI 챗봇 상담
- 고용노동 정책에 관한 자유로운 질의응답
- RAG(Retrieval-Augmented Generation) 기술을 활용한 정확한 정보 제공
- 사용자 프로필 기반 맞춤형 정책 안내

![챗봇 화면](./docs/imgs/chatbot.png)

### 🔎 정책 검색 및 조회
- 키워드 기반 정책 검색 기능
- 카테고리별 정책 필터링 및 조회
- 정책 상세 정보 제공

![정책검색 화면](./docs/imgs/policy_search.png)

## 🌀 아키텍처

```
+---------------------+       +------------------------+
|                     |       |                        |
|   Frontend (React)  | <---> |   Backend (FastAPI)    |
|                     |       |                        |
+---------------------+       +------------------------+
                                         |
                                         | 
                                         v
              +-------------------------------------------+
              |                                           |
              |  +-------------+        +-------------+   |
              |  |             |        |             |   |
              |  |   MySQL     |        |  Pinecone   |   |
              |  |  Database   |        | Vector DB   |   |
              |  |             |        |             |   |
              |  +-------------+        +-------------+   |
              |                                           |
              |           Data Storage Layer              |
              +-------------------------------------------+
                                         |
                                         |
                                         v
              +-------------------------------------------+
              |                                           |
              |  +-------------+        +-------------+   |
              |  |             |        |             |   |
              |  |  OpenAI API |        |   OCR API   |   |
              |  |  (LLM/Embed)|        | (Naver Cloud)|  |
              |  |             |        |             |   |
              |  +-------------+        +-------------+   |
              |                                           |
              |             AI Service Layer              |
              +-------------------------------------------+
                                         ^
                                         |
              +-------------------------------------------+
              |                                           |
              |        Data Processing Pipeline           |
              |  (PDF -> OCR -> Chunking -> Embedding)    |
              |                                           |
              +-------------------------------------------+
```

## 📊 데이터 파이프라인

프로젝트의 핵심은 고용노동부 정책 문서를 처리하는 파이프라인입니다:

```
PDF 문서 -> OCR/텍스트 추출 -> 전처리 -> 청크 분할 -> 임베딩 생성 -> 벡터 DB 저장
```

1. **OCR 처리**: 
   - 이미지 기반 PDF에서 텍스트를 추출하기 위해 여러 OCR 기술 비교 테스트
   - Naver Cloud OCR API 채택 (가장 높은 정확도)

2. **데이터 청킹 및 임베딩**: 
   - 추출된 텍스트를 의미 있는 단위로 분할
   - OpenAI의 임베딩 모델을 사용해 벡터화

3. **벡터 데이터베이스 저장**: 
   - 생성된 임베딩을 Pinecone 벡터 DB에 저장
   - 의미 기반 검색 지원

4. **RAG(Retrieval-Augmented Generation) 시스템**: 
   - 사용자 질문 임베딩 → 유사 문서 검색 → LLM에 컨텍스트 제공 → 정확한 응답 생성

## 🛠️ 설치 및 실행

### 1️⃣ 환경 설정

```bash
# 저장소 클론
git clone https://github.com/yourusername/labor-policy-assistant.git
cd labor-policy-assistant

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 라이브러리 설치
pip install -r requirements.txt
```

### 2️⃣ 환경 변수 설정

`.env` 파일을 생성하고 다음 변수를 설정:

```
# API 키
OPENAI_API_KEY=your-openai-api-key
PINECONE_API_KEY=your-pinecone-api-key
NAVER_CLOVA_SECRET_KEY=your-naver-api-key
NAVER_CLOVA_API_URL=your-naver-api-url

# 데이터베이스
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DB=labor_policy
MYSQL_PORT=3306

# JWT
SECRET_KEY=your-secret-key-for-jwt
```

### 3️⃣ 백엔드 실행

```bash
cd backend
uvicorn app.main:app --reload
```

### 4️⃣ 프론트엔드 실행

```bash
cd frontend
npm install
npm start
```

## 📡 API 목록

| API 엔드포인트              | 메소드 | 설명                                |
|-----------------------------|--------|-------------------------------------|
| `/api/auth/register`        | POST   | 사용자 회원가입                     |
| `/api/auth/login`           | POST   | 사용자 로그인 및 토큰 발급          |
| `/api/auth/me`              | GET    | 현재 로그인한 사용자 정보 조회      |
| `/api/policies`             | GET    | 정책 목록 조회                      |
| `/api/policies/{id}`        | GET    | 특정 정책 상세 조회                 |
| `/api/policies/search`      | GET    | 정책 검색 (타이틀 및 설명 기반)     |
| `/api/profiles`             | POST   | 사용자 프로필 생성 및 업데이트      |
| `/api/profiles/{user_id}`   | GET    | 특정 사용자의 프로필 조회           |
| `/api/recommendations`      | POST   | 사용자 프로필 기반 정책 추천        |
| `/api/chat`                 | POST   | AI 챗봇 질의응답                    |



## 👤 개발자 정보

| 이름   | GitHub                          | 역할        |
|--------|--------------------------------|------------|
| 강현구 | [@ardkyer](https://github.com/ardkyer) | Backend / Frontend / AI   |
