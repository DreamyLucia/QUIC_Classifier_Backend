from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, user, upload
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(title="QUIC Classifier API", version="1.0.0")

# 启动时初始化数据库
init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(upload.router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "QUIC Classifier API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"  # FastAPI 自动生成的文档地址
    }