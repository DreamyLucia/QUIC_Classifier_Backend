from pydantic import BaseModel
from typing import List, Optional, Dict


class DailyStats(BaseModel):
    """每日统计"""
    date: str  # 格式: 2025-03-24
    total: int  # 当日分析文件数
    category_stats: Dict[str, int]  # 当日各类别统计
    unknown_count: int  # 当日未识别数
    avg_confidence: float  # 当日平均置信度
    total_analysis_time: float  # 当日总分析耗时（秒）


class UserAllStatsResponse(BaseModel):
    """用户总览统计响应"""
    total: int
    category_stats: Dict[str, int]
    unknown_count: int
    total_analysis_time: float
    avg_confidence: float


class UserDailyStatsResponse(BaseModel):
    """用户按日统计响应"""
    daily_stats: List[DailyStats]
    start_date: Optional[str]
    end_date: Optional[str]