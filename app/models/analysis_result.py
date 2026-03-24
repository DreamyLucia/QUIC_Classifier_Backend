from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, func
from app.core.database import Base


class AnalysisResult(Base):
    """分析结果表"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, index=True,
                     comment="任务ID")
    user_id = Column(String(12), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False, comment="原始文件名")
    saved_name = Column(String(255), nullable=False, comment="保存的文件名")
    label = Column(String(50), nullable=False, comment="预测类别")
    confidence = Column(Float, nullable=False, comment="置信度")
    probabilities = Column(JSON, nullable=False, comment="所有类别概率")
    file_size = Column(Integer, nullable=False, comment="文件大小(字节)")
    analysis_time = Column(Float, nullable=True, comment="分析耗时(秒)")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<AnalysisResult(task_id={self.task_id}, filename={self.filename}, label={self.label})>"