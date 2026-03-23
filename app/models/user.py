from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(8), primary_key=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码哈希")
    role = Column(String(20), default="user", nullable=False, comment="角色: admin/user")  # ← 新增
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"