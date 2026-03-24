# app/api/v1/endpoints/upload.py
import os
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.task import Task
from app.core.config import settings
from app.services.analysis_service import AnalysisService
import asyncio
from app.schemas.upload import BatchUploadResponse, FailedFile
from app.utils.response import APIResponse

router = APIRouter(prefix="/upload", tags=["上传"])

ALLOWED_EXTENSIONS = {'.pcap', '.cap'}
MAX_FILE_SIZE = 100 * 1024 * 1024

PCAP_MAGIC_NUMBERS = [
    b'\xd4\xc3\xb2\xa1',
    b'\xa1\xb2\xc3\xd4',
    b'\x4d\x3c\xb2\xa1',
    b'\xa1\xb2\x3c\x4d',
]

# 类别列表
CLASS_NAMES = ['Nkiri', 'bilibili', 'edge', 'kwai',
               'tencentnews', 'tencentvideo', 'tiktok', 'xiaohongshu']


def is_valid_pcap(file_path: str) -> bool:
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header in PCAP_MAGIC_NUMBERS
    except Exception:
        return False


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def generate_task_name() -> str:
    """生成任务名称"""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


async def save_file_safe(task_dir: Path, file: UploadFile) -> tuple:
    """
    安全保存单个文件
    返回: (original_name, saved_name, size, success, error_msg)
    """
    tmp_path = None
    try:
        # 验证文件类型
        if not allowed_file(file.filename):
            return (file.filename, None, 0, False, "不支持的文件格式")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(file.filename)[1],
                dir=task_dir
        ) as tmp:
            tmp_path = tmp.name

        # 接收文件内容
        content = await file.read()

        # 验证文件大小
        if len(content) > MAX_FILE_SIZE:
            return (file.filename, None, 0, False, f"文件过大，最大 {MAX_FILE_SIZE // (1024 * 1024)}MB")

        # 写入临时文件
        with open(tmp_path, 'wb') as f:
            f.write(content)

        # 验证 pcap 文件完整性
        if not is_valid_pcap(tmp_path):
            return (file.filename, None, 0, False, "无效的 pcap 文件")

        # 生成最终文件名（处理重名）
        original_name = file.filename
        base_name = os.path.splitext(original_name)[0]
        ext = os.path.splitext(original_name)[1]

        final_name = original_name
        counter = 1
        while (task_dir / final_name).exists():
            final_name = f"{base_name}_{counter}{ext}"
            counter += 1

        final_path = task_dir / final_name
        os.rename(tmp_path, final_path)

        return (original_name, final_name, len(content), True, None)

    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return (file.filename, None, 0, False, str(e))


@router.post("/batch", response_model=BatchUploadResponse)
async def upload_batch_pcap(
        files: list[UploadFile] = File(...),
        task_id: str = Query(..., description="任务ID"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 验证参数
    if not task_id:
        raise HTTPException(status_code=400, detail="task_id 不能为空")

    if not files:
        raise HTTPException(status_code=400, detail="没有要上传的文件")

    # 创建或获取任务记录
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        task_name = generate_task_name()
        task = Task(
            task_id=task_id,
            user_id=current_user.id,
            task_name=task_name,
            file_count=0,
            category_stats={cat: 0 for cat in CLASS_NAMES},
            unknown_count=0,
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)

    # 创建任务目录
    task_dir = settings.UPLOAD_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    # 逐个保存文件，只记录成功的
    success_count = 0
    fail_count = 0
    failed_files = []

    for file in files:
        # 调用 save_file_safe 保存文件
        original_name, saved_name, size, success, error_msg = await save_file_safe(task_dir, file)

        if success:
            success_count += 1
        else:
            fail_count += 1
            failed_files.append({"filename": original_name, "error": error_msg})

    # 更新任务记录（只记录成功的文件数）
    task.file_count = success_count

    # 构建失败文件列表
    failed_files_list = [
        {"filename": f["filename"], "error": f["error"]}
        for f in failed_files
    ] if failed_files else None

    if success_count == 0:
        task.status = "failed"
    else:
        task.status = "pending"  # 等待分析

    db.commit()

    # 如果有成功的文件，触发分析
    if success_count > 0:
        analysis_service = AnalysisService()
        asyncio.create_task(analysis_service.analyze_task(task_id, db))

    # 返回结果
    return APIResponse.success(
        data={
            "task_id": task_id,
            "task_name": task.task_name,
            "total": len(files),
            "success": success_count,
            "failed": fail_count,
            "failed_files": failed_files_list
        },
        msg="上传完成，等待分析"
    )