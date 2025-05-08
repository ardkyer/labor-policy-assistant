<div align="center">
  <br>
  <img width="1275" alt="image" src="https://github.com/user-attachments/assets/3dbc2926-fd9c-4be1-8b6e-aec181659106" />

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
<br>
<br>

## 🚀 프로젝트 소개
Labor Policy AI Assistant는 고용노동부의 방대한 정책 정보를 쉽게 찾고 활용할 수 있도록 돕는 **AI 기반 정책 추천 및 상담 서비스**입니다.  
이 프로젝트는 **제4회 고용노동 공공데이터 활용 공모전**에 제출되었으며, 319페이지에 달하는 '한권으로 통하는 고용노동정책' PDF 자료를 AI 기술로 분석하여 개인 맞춤형 서비스를 제공합니다.

🔹 **AI 기반 정책 매칭**: 사용자의 프로필(나이, 성별, 취업 상태 등)을 기반으로 적합한 정책 추천  
🔹 **LLM 기반 질의응답**: 고용노동 정책에 관한 자유로운 질의응답 서비스  

<br>
<br>
<br>

## 🏗️ 기능 소개

### 🔑 회원가입 및 로그인
- 사용자 프로필 기반 맞춤형 서비스 제공을 위한 회원 관리 시스템
- 나이, 성별, 취업 상태 등 정책 추천에 필요한 프로필 정보 입력

<img width="952" alt="image" src="https://github.com/user-attachments/assets/a19f909b-35a7-40c7-8766-d2b231f7c0fa" />

<br>

<img width="955" alt="image" src="https://github.com/user-attachments/assets/d6810a2a-8760-49e9-b8bc-a2d83936174f" />

<br>
<br>
<br>


### 🔍 맞춤형 정책 추천
- 사용자 프로필에 기반한 개인화된 정책 추천
- 추천 정책의 요약 정보 및 원문 PDF 다운로드 제공

<img width="958" alt="image" src="https://github.com/user-attachments/assets/65fc8824-6b0f-4a3e-a968-1a81d0c8991e" />

<br>

<img width="952" alt="image" src="https://github.com/user-attachments/assets/880661d5-cf49-4a27-8619-83734dfa966f" />

<br>
<br>
<br>
<br>

### 💬 AI 챗봇 상담
- 고용노동 정책에 관한 자유로운 질의응답
- RAG(Retrieval-Augmented Generation) 기술을 활용한 정확한 정보 제공
- 사용자 프로필 기반 맞춤형 정책 안내

<img width="950" alt="image" src="https://github.com/user-attachments/assets/17944ae9-e911-4989-9ccc-18844c58aa2d" />

<br>

<img width="950" alt="image" src="https://github.com/user-attachments/assets/852b2165-7e40-4e86-9d2d-992cbc6c3597" />

<br>

<img width="953" alt="image" src="https://github.com/user-attachments/assets/83aef5ff-3ef1-4a67-b088-9cdb0407dc42" />

<br>
<br>
<br>

## 🌀 아키텍처

<img width="1262" alt="image" src="https://github.com/user-attachments/assets/2cd88dec-4636-44c9-ad74-0b1d8884753e" />



## 📊 데이터 파이프라인

```
PDF 문서 -> OCR/텍스트 추출 -> 전처리 -> 청크 분할 -> 임베딩 생성 -> 벡터 DB 저장
```

1. **OCR 처리**: 
   - 이미지 기반 PDF에서 텍스트를 추출하기 위해 여러 OCR 기술 비교 테스트
   - Naver Cloud OCR API 채택 (가장 높은 정확도)

2. **데이터 청킹 및 임베딩**: 
   - LangChain의 RecursiveCharacterTextSplitter를 사용하여 추출된 텍스트를 의미 있는 단위로 분할
   - OpenAI의 text-embedding-3-small 모델을 사용해 텍스트 청크를 1536차원 벡터로 변환

3. **벡터 데이터베이스 저장**: 
   - LangChain 벡터 저장소 인터페이스를 통해 생성된 임베딩을 Pinecone 벡터 DB에 저장
   - 텍스트 내용과 페이지 정보를 메타데이터로 함께 저장하여 검색 시 활용

4. **RAG(Retrieval-Augmented Generation) 시스템**: 
   - LangChain의 검색 체인을 활용하여 사용자 질문 임베딩 → 유사 문서 검색 → LLM에 컨텍스트 제공 → 정확한 응답 생성
   - LangChain의 RetrievalQA 체인으로 검색-증강-생성 과정을 통합 구현

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

<br>
<br>

## 개발일지

[제4회 고용노동 공공데이터 활용 공모전 탐색](https://ardkyer.github.io/dev_logs/공모전-준비/)  
[pdf 파서해서 pinecone에 넣기](https://ardkyer.github.io/dev_logs/pdf-파서해서-pinecone에-넣기/)  
[PDF OCR하기](https://ardkyer.github.io/dev_logs/PDF-OCR-하기/)  
[OCR 채택](https://ardkyer.github.io/dev_logs/OCR-채택/)  
[고용노동부 어시스턴트 API 개발 및 테스트](https://ardkyer.github.io/dev_logs/고용노동부-API-개발/)  
[OCR중 critical한 문제 해결](https://ardkyer.github.io/dev_logs/OCR중-critical한-오류-발생/)  
[PDF 100장 넣고 테스트](https://ardkyer.github.io/dev_logs/2025-03-29-PDF-100장-넣고-테스트/)  
[백엔드, 프론트엔드 연동](https://ardkyer.github.io/dev_logs/백엔드,-프론트엔드-연동-테스트/)  
[프론트엔드 마무리 작업](https://ardkyer.github.io/dev_logs/프론트엔드-마무리-작업/)  
[공공데이터 공모전 사업계획서 작성](https://ardkyer.github.io/dev_logs/공공데이터공모전_사업계획서/)  


## 👤 개발자 정보

| 이름   | GitHub                          | 역할        |
|--------|--------------------------------|------------|
| 강현구 | [@ardkyer](https://github.com/ardkyer) | Backend / Frontend / AI   |
