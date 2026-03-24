# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 使用配置文件中的数据库 URL
DATABASE_URL = settings.DATABASE_URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 连接池预检，自动重连
    pool_recycle=3600,  # 连接回收时间（秒），防止 MySQL 超时断开
    echo=settings.DEBUG,  # 开发环境打印 SQL 语句，方便调试
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,  # 不自动提交
    autoflush=False,  # 不自动刷新
    bind=engine,  # 绑定数据库引擎
)

# 创建基类（所有模型都要继承这个类）
Base = declarative_base()


def get_db():
    """
    获取数据库会话（依赖注入用）
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    from app.models.user import User
    from app.models.task import Task
    from app.models.analysis_result import AnalysisResult

    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")
