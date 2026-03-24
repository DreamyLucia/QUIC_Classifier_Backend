# app/services/analysis_service.py
import time
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.task import Task
from app.models.analysis_result import AnalysisResult
from app.ml.feature_extractor import FeatureExtractor
from app.ml.model_engine import ModelEngine
import shutil

# 类别列表
CLASS_NAMES = ['Nkiri', 'bilibili', 'edge', 'kwai',
               'tencentnews', 'tencentvideo', 'tiktok', 'xiaohongshu']


class AnalysisService:
    def __init__(self):
        # 权重文件路径
        weights_dir = Path(__file__).parent.parent.parent / "models" / "weights"

        print(f"权重目录: {weights_dir}")
        print(f"TemporalCNN 存在: {(weights_dir / 'TemporalCNN_best.pth').exists()}")
        print(f"PayloadCNN 存在: {(weights_dir / 'PayloadCNN_best.pth').exists()}")
        print(f"nb_classifier 存在: {(weights_dir / 'nb_classifier.pkl').exists()}")

        self.feature_extractor = FeatureExtractor()
        self.model_engine = ModelEngine(
            time_model_path=str(weights_dir / "TemporalCNN_best.pth"),
            byte_model_path=str(weights_dir / "PayloadCNN_best.pth"),
            nb_clf_path=str(weights_dir / "nb_classifier.pkl")
        )
        print("分析服务初始化成功")

    async def analyze_task(self, task_id: str, db: Session) -> Dict[str, Any]:
        """分析任务中的所有文件"""

        if self.model_engine is None:
            return {"error": "模型服务未初始化"}

        # 获取任务
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return {"error": "任务不存在"}

        # 更新状态为分析中
        task.status = "analyzing"
        db.commit()

        # 获取任务文件目录
        task_dir = settings.UPLOAD_DIR / task_id
        if not task_dir.exists():
            task.status = "failed"
            db.commit()
            return {"error": "任务文件目录不存在"}

        # 获取所有 pcap 文件
        pcap_files = list(task_dir.glob("*.pcap")) + list(task_dir.glob("*.cap"))
        if not pcap_files:
            task.status = "failed"
            db.commit()
            return {"error": "没有找到 pcap 文件"}

        # 初始化统计
        category_stats = {cat: 0 for cat in CLASS_NAMES}
        unknown_count = 0

        # 逐个分析文件
        for pcap_file in pcap_files:
            start_time = time.time()

            try:
                # 提取特征
                features = self.feature_extractor.extract_from_pcap(str(pcap_file))
                if features is None:
                    raise ValueError("特征提取失败")

                # 模型预测
                result = self.model_engine.predict(features)

                analysis_time = time.time() - start_time

                # 保存到 analysis_results 表
                analysis_result = AnalysisResult(
                    task_id=task_id,
                    user_id=task.user_id,
                    filename=pcap_file.name,
                    saved_name=pcap_file.name,
                    label=result["label"],
                    confidence=result["confidence"],
                    probabilities=result["probabilities"],
                    file_size=pcap_file.stat().st_size,
                    analysis_time=analysis_time
                )
                db.add(analysis_result)
                db.commit()

                # 更新统计
                if result["label"] in category_stats:
                    category_stats[result["label"]] += 1
                else:
                    unknown_count += 1

                print(f"✅ 分析完成: {pcap_file.name} → {result['label']} ({result['confidence']:.2f})")

            except Exception as e:
                print(f"❌ 分析文件 {pcap_file.name} 失败: {e}")
                unknown_count += 1

        # 更新任务统计
        task.category_stats = category_stats
        task.unknown_count = unknown_count
        task.status = "completed"
        db.commit()

        print(f"任务 {task_id} 分析完成: 总计 {len(pcap_files)} 个文件")
        print(f"统计: {category_stats}")

        # 分析完成后，自动删除原始 pcap 文件（释放空间）
        task_dir = settings.UPLOAD_DIR / task_id
        if task_dir.exists():
            try:
                shutil.rmtree(task_dir)
                print(f"✅ 已删除任务 {task_id} 的原始文件，释放空间")
            except Exception as e:
                print(f"❌ 删除任务文件失败: {e}")

        return {
            "task_id": task_id,
            "task_name": task.task_name,
            "total": len(pcap_files),
            "category_stats": category_stats,
            "unknown_count": unknown_count
        }