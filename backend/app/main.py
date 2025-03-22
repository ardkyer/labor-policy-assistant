from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, policies, profiles, chat

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="고용노동부 정책 지원 어시스턴트 API",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["인증"])
app.include_router(policies.router, prefix=f"{settings.API_V1_STR}/policies", tags=["정책"])
app.include_router(profiles.router, prefix=f"{settings.API_V1_STR}/profiles", tags=["프로필"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["챗봇"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)