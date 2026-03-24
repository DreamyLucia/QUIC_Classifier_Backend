from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, cast, Date
from datetime import datetime, timedelta
from typing import Optional
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.analysis_result import AnalysisResult
from app.utils.response import APIResponse
from app.schemas.results import UserAllStatsResponse, UserDailyStatsResponse, DailyStats

router = APIRouter(prefix="/results", tags=["分析结果"])

# 类别列表
CLASS_NAMES = ['Nkiri', 'bilibili', 'edge', 'kwai',
               'tencentnews', 'tencentvideo', 'tiktok', 'xiaohongshu']


@router.get("/user/all")
async def get_user_all_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取当前用户的所有分析结果概览

    返回:
    - total: 总分析文件数
    - category_stats: 各类别数量统计
    - unknown_count: 未识别数量
    - total_analysis_time: 总分析耗时（秒）
    - avg_confidence: 平均置信度
    """

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

    data = UserAllStatsResponse(
        total=total_count,
        category_stats=category_stats,
        unknown_count=unknown_count,
        total_analysis_time=round(total_analysis_time, 2),
        avg_confidence=round(avg_confidence, 4)
    )

    return APIResponse.success(data=data.model_dump())


@router.get("/user/daily")
async def get_user_daily_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        days: int = Query(7, ge=1, le=90, description="最近N天，默认7天")
):
    """
    获取当前用户按日统计的分析结果（用于折线图）

    返回最近 N 天的每日统计数据:
    - date: 日期
    - total: 当日分析文件数
    - category_stats: 当日各类别统计
    - unknown_count: 当日未识别数
    - avg_confidence: 当日平均置信度
    - total_analysis_time: 当日总分析耗时
    """

    # 计算起始日期
    start_date = (datetime.now() - timedelta(days=days - 1)).date()

    # 构建查询 - 获取每日总数
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

        # 查询该日各类别数量
        category_query = db.query(
            AnalysisResult.label,
            func.count(AnalysisResult.id).label("count")
        ).filter(
            AnalysisResult.user_id == current_user.id,
            func.date(AnalysisResult.created_at) == day_total.date
        ).group_by(AnalysisResult.label).all()

        # 初始化类别统计
        category_stats = {cat: 0 for cat in CLASS_NAMES}
        unknown_count = 0

        for cat_result in category_query:
            if cat_result.label in category_stats:
                category_stats[cat_result.label] = cat_result.count
            else:
                unknown_count += cat_result.count

        daily_stats.append(DailyStats(
            date=date_str,
            total=day_total.total,
            category_stats=category_stats,
            unknown_count=unknown_count,
            avg_confidence=round(day_total.avg_confidence, 4) if day_total.avg_confidence else 0,
            total_analysis_time=round(day_total.total_analysis_time, 2) if day_total.total_analysis_time else 0
        ))

    # 补全没有数据的日期（返回 0 值）
    result_stats = []
    current_date = start_date
    end_date = datetime.now().date()

    # 将已有的数据转为字典方便查找
    stats_dict = {s.date: s for s in daily_stats}

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in stats_dict:
            result_stats.append(stats_dict[date_str])
        else:
            # 没有数据的日期，返回空统计
            result_stats.append(DailyStats(
                date=date_str,
                total=0,
                category_stats={cat: 0 for cat in CLASS_NAMES},
                unknown_count=0,
                avg_confidence=0,
                total_analysis_time=0
            ))
        current_date += timedelta(days=1)

    data = UserDailyStatsResponse(
        daily_stats=[d.model_dump() for d in result_stats],
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )

    return APIResponse.success(data=data.model_dump())


@router.get("/task/{task_id}")
async def get_task_results(
        task_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    获取指定任务的详细分析结果

    返回:
    - task_id
    - task_name
    - total: 总分析文件数
    - category_stats: 各类别数量统计
    - unknown_count: 未识别数量
    - total_analysis_time: 总分析耗时
    - avg_confidence: 平均置信度
    - results: 每个文件的分析结果列表
    """

    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限访问")

    results = db.query(AnalysisResult).filter(
        AnalysisResult.task_id == task_id
    ).order_by(AnalysisResult.created_at).all()

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
        "task_id": task_id,
        "task_name": task.task_name,
        "total": total_count,
        "category_stats": category_stats,
        "unknown_count": unknown_count,
        "total_analysis_time": round(total_analysis_time, 2),
        "avg_confidence": round(avg_confidence, 4),
        "results": [
            {
                "filename": r.filename,
                "label": r.label,
                "confidence": r.confidence,
                "analysis_time": r.analysis_time,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    })