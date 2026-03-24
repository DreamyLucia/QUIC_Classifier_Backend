from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from app.core.database import Base


class UploadRecord(Base):
    """上传记录表"""
    __tablename__ = "upload_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False, comment="任务ID")
    user_id = Column(String(12), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    task_name = Column(String(255), nullable=False, comment="任务名称（创建时间字符串）")
    file_count = Column(Integer, default=0, comment="文件总数")

    # 八种流量包统计（JSON 格式，存储各类型数量）
    category_stats = Column(JSON, default=dict, comment="各类型统计: {bilibili: 5, tiktok: 3, ...}")

    # 未识别出的数量
    unknown_count = Column(Integer, default=0, comment="未识别出的数量")

    # 任务状态: pending, analyzing, completed, failed
    status = Column(String(20), default="pending", comment="任务状态")

    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<UploadRecord(task_id={self.task_id}, task_name={self.task_name}, user_id={self.user_id})>"