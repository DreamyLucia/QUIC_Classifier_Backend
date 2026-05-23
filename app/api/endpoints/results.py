from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional
from app.api.dependencies import get_current_user
from app.utils.response import APIResponse
from app.core.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.analysis_result import AnalysisResult
from app.schemas.results import (
    UserAllStatsResponse,
    UserDailyStatsResponse,
    DailyStats,
    TaskInfo,
    TaskResultItem,
    TaskResultsResponse,
    UserTasksResponse
)

router = APIRouter(prefix="/results", tags=["分析结果"])

# 类别列表
CLASS_NAMES = ['Nkiri', 'bilibili', 'edge', 'kwai',
               'tencentnews', 'tencentvideo', 'tiktok', 'xiaohongshu']


@router.get("/user/all", response_model=UserAllStatsResponse)
async def get_user_all_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取当前用户的所有分析结果概览"""

    results = db.query(AnalysisResult).filter(
        AnalysisResult.user_id == current_user.id
    ).all()

    category_stats = {cat: 0 for cat in CLASS_NAMES}
    unknown_count = 0
    total_analysis_time = 0.0
    total_confidence = 0.0

    for r in results:
        if r.label in category_stats:
            category_stats[r.label] += 1
        else:
            unknown_count += 1

        if r.analysis_time:
            total_analysis_time += r.analysis_time
        if r.confidence:
            total_confidence += r.confidence

    total_count = len(results)
    avg_confidence = total_confidence / total_count if total_count > 0 else 0

    return APIResponse.success(data={
        "total": total_count,
        "category_stats": category_stats,
        "unknown_count": unknown_count,
        "total_analysis_time": round(total_analysis_time, 2),
        "avg_confidence": round(avg_confidence, 4)
    }, msg="success")


@router.get("/user/daily", response_model=UserDailyStatsResponse)
async def get_user_daily_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        days: int = Query(7, ge=1, le=90, description="最近N天，默认7天")
):
    """获取当前用户最近N天的每日统计（用于折线图）"""

    # 计算起始日期（最近 days 天）
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    end_date = datetime.now().date()

    # 查询每日汇总数据
    query = db.query(
        func.date(AnalysisResult.created_at).label("date"),
        func.count(AnalysisResult.id).label("total"),
        func.sum(AnalysisResult.analysis_time).label("total_analysis_time"),
        func.avg(AnalysisResult.confidence).label("avg_confidence")
    ).filter(
        AnalysisResult.user_id == current_user.id,
        func.date(AnalysisResult.created_at) >= start_date
    ).group_by(func.date(AnalysisResult.created_at)).order_by(
        func.date(AnalysisResult.created_at)
    )

    daily_totals = query.all()

    # 获取每日的类别统计
    daily_stats = []

    for day_total in daily_totals:
        date_str = day_total.date.strftime("%Y-%m-%d")

        category_query = db.query(
            AnalysisResult.label,
            func.count(AnalysisResult.id).label("count")
        ).filter(
            AnalysisResult.user_id == current_user.id,
            func.date(AnalysisResult.created_at) == day_total.date
        ).group_by(AnalysisResult.label).all()

        category_stats = {cat: 0 for cat in CLASS_NAMES}
        unknown_count = 0

        for cat_result in category_query:
            if cat_result.label in category_stats:
                category_stats[cat_result.label] = cat_result.count
            else:
                unknown_count += cat_result.count

        daily_stats.append(DailyStats(
            date=date_str,
            file_count=day_total.total,
            category_stats=category_stats,
            unknown_count=unknown_count,
            avg_confidence=round(day_total.avg_confidence, 4) if day_total.avg_confidence else 0,
            total_analysis_time=round(day_total.total_analysis_time, 2) if day_total.total_analysis_time else 0
        ))

    # 补全没有数据的日期
    result_stats = []
    current_date = start_date
    stats_dict = {s.date: s for s in daily_stats}

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in stats_dict:
            result_stats.append(stats_dict[date_str])
        else:
            result_stats.append(DailyStats(
                date=date_str,
                file_count=0,
                category_stats={cat: 0 for cat in CLASS_NAMES},
                unknown_count=0,
                avg_confidence=0,
                total_analysis_time=0
            ))
        current_date += timedelta(days=1)

    return APIResponse.success(data={
        "daily_stats": [d.model_dump() for d in result_stats],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }, msg="success")


@router.get("/tasks", response_model=UserTasksResponse)
async def get_user_tasks(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        status: Optional[str] = Query(None, description="任务状态: pending/analyzing/completed/failed")
):
    """
    获取当前用户的所有任务列表（摘要信息）

    返回每个任务的摘要信息:
    - task_id
    - task_name
    - file_count: 文件总数
    - status: 任务状态
    - category_stats: 各类别统计
    - unknown_count: 未识别数量
    - created_at: 创建时间
    - updated_at: 更新时间
    """

    query = db.query(Task).filter(Task.user_id == current_user.id)

    if status:
        query = query.filter(Task.status == status)

    tasks = query.order_by(desc(Task.created_at)).all()

    task_infos = []
    for t in tasks:
        # 查询该任务的所有分析结果
        results = db.query(AnalysisResult).filter(
            AnalysisResult.task_id == t.task_id
        ).all()

        # 计算总分析耗时和平均置信度
        total_analysis_time = sum(r.analysis_time or 0 for r in results)
        total_confidence = sum(r.confidence or 0 for r in results)
        result_count = len(results)
        avg_confidence = total_confidence / result_count if result_count > 0 else 0

        task_infos.append(TaskInfo(
            task_id=t.task_id,
            task_name=t.task_name,
            file_count=t.file_count,
            status=t.status,
            model_type=t.model_type,
            category_stats=t.category_stats,
            unknown_count=t.unknown_count,
            total_analysis_time=round(total_analysis_time, 2),
            avg_confidence=round(avg_confidence, 4),
            created_at=t.created_at.isoformat() if t.created_at else None,
            updated_at=t.updated_at.isoformat() if t.updated_at else None
        ))

    return APIResponse.success(data={
        "total": len(tasks),
        "tasks": [t.model_dump() for t in task_infos]
    }, msg="success")


@router.get("/task/{task_id}", response_model=TaskResultsResponse)
async def get_task_results(
        task_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取指定任务的详细分析结果

    返回:
    - 任务摘要信息
    - 每个文件的分析结果列表
    """

    # 获取任务信息
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 权限检查
    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限访问")

    # 获取分析结果
    results = db.query(AnalysisResult).filter(
        AnalysisResult.task_id == task_id
    ).order_by(AnalysisResult.created_at).all()

    # 统计
    category_stats = {cat: 0 for cat in CLASS_NAMES}
    unknown_count = 0
    total_analysis_time = 0.0
    total_confidence = 0.0

    for r in results:
        if r.label in category_stats:
            category_stats[r.label] += 1
        else:
            unknown_count += 1

        if r.analysis_time:
            total_analysis_time += r.analysis_time
        if r.confidence:
            total_confidence += r.confidence

    total_count = len(results)
    avg_confidence = total_confidence / total_count if total_count > 0 else 0

    # 构建结果列表
    result_items = [
        {
            "filename": r.filename,
            "label": r.label,
            "confidence": r.confidence,
            "probabilities": r.probabilities,
            "analysis_time": r.analysis_time,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in results
    ]

    return APIResponse.success(data={
        "task_id": task.task_id,
        "task_name": task.task_name,
        "file_count": task.file_count,
        "status": task.status,
        "model_type": task.model_type,
        "category_stats": category_stats,
        "unknown_count": unknown_count,
        "total_analysis_time": round(total_analysis_time, 2),
        "avg_confidence": round(avg_confidence, 4),
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "results": result_items
    }, msg="success")