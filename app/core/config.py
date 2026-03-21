import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    # 项目根目录
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR = BASE_DIR / "uploads"

    # JWT 配置
    JWT_SECRET = os.getenv("JWT_SECRET", "fallback-secret-key-change-this")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # CORS 配置
    _cors_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5004")
    ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(",")]

    # RSA 密钥路径
    PRIVATE_KEY_PATH = BASE_DIR / "private_key.pem"
    PUBLIC_KEY_PATH = BASE_DIR / "public_key.pem"

    # 数据库配置
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "quic_db")
    DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接 URL"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )

    # 调试模式
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()