from pydantic import BaseModel
from typing import List, Optional


class FailedFile(BaseModel):
    """失败文件信息"""
    filename: str
    error: str


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    task_id: str
    task_name: str
    total: int
    success: int
    failed: int
    failed_files: Optional[List[FailedFile]] = None