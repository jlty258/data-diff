"""
MigrationAgent - 数据迁移代理核心实现
"""

import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from data_diff import connect_to_table, diff_tables, Algorithm
from data_diff.databases import Database
from data_diff.databases._connect import connect
from data_diff.migration.sql_translator import SQLTranslator, DatabaseDialect
from data_diff.migration.validator import MigrationValidator
from data_diff.utils import getLogger

logger = getLogger(__name__)


class MigrationStatus(Enum):
    """迁移状态"""
    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    VALIDATING = "validating"  # 验证中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class MigrationTask:
    """迁移任务"""
    task_id: str
    source_database: str
    target_database: str
    source_table: str
    target_table: str
    key_columns: Tuple[str, ...] = ("id",)
    update_column: Optional[str] = None
    extra_columns: Tuple[str, ...] = ()
    
    # SQL 转换配置
    sql_files: List[str] = field(default_factory=list)  # 需要转换的 SQL 文件
    sql_statements: List[str] = field(default_factory=list)  # 需要转换的 SQL 语句
    
    # 验证配置
    validate_after_migration: bool = True
    validation_threshold: float = 0.0  # 允许的差异百分比阈值
    
    # 元数据
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationProgress:
    """迁移进度"""
    task_id: str
    status: MigrationStatus
    progress_percent: float = 0.0
    current_step: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    stats: Dict[str, Any] = field(default_factory=dict)


class MigrationAgent:
    """数据迁移代理"""
    
    def __init__(self):
        self.tasks: Dict[str, MigrationTask] = {}
        self.progress: Dict[str, MigrationProgress] = {}
        self.sql_translator = SQLTranslator()
        self.validator = MigrationValidator()
    
    def create_task(self, task: MigrationTask) -> str:
        """创建迁移任务"""
        if task.task_id in self.tasks:
            raise ValueError(f"任务 ID '{task.task_id}' 已存在")
        
        self.tasks[task.task_id] = task
        self.progress[task.task_id] = MigrationProgress(
            task_id=task.task_id,
            status=MigrationStatus.PENDING
        )
        
        logger.info(f"创建迁移任务: {task.task_id}")
        return task.task_id
    
    def get_task(self, task_id: str) -> Optional[MigrationTask]:
        """获取迁移任务"""
        return self.tasks.get(task_id)
    
    def get_progress(self, task_id: str) -> Optional[MigrationProgress]:
        """获取迁移进度"""
        return self.progress.get(task_id)
    
    def execute_migration(self, task_id: str) -> MigrationProgress:
        """执行迁移任务"""
        if task_id not in self.tasks:
            raise ValueError(f"任务 ID '{task_id}' 不存在")
        
        task = self.tasks[task_id]
        progress = self.progress[task_id]
        
        progress.status = MigrationStatus.RUNNING
        progress.started_at = datetime.now()
        progress.current_step = "开始迁移"
        
        try:
            # 步骤1: SQL 转换
            if task.sql_files or task.sql_statements:
                progress.current_step = "转换 SQL 语句"
                progress.progress_percent = 10.0
                self._translate_sql(task, progress)
            
            # 步骤2: 数据迁移（这里只是示例，实际需要调用具体的迁移工具）
            progress.current_step = "执行数据迁移"
            progress.progress_percent = 30.0
            # 注意：实际的数据迁移需要调用具体的数据迁移工具
            # 这里只是占位，实际实现需要根据具体需求
            
            # 步骤3: 验证迁移结果
            if task.validate_after_migration:
                progress.current_step = "验证迁移结果"
                progress.status = MigrationStatus.VALIDATING
                progress.progress_percent = 80.0
                validation_result = self._validate_migration(task, progress)
                
                if not validation_result["success"]:
                    progress.status = MigrationStatus.FAILED
                    progress.error = f"验证失败: {validation_result.get('error')}"
                    return progress
            
            # 完成
            progress.status = MigrationStatus.COMPLETED
            progress.progress_percent = 100.0
            progress.completed_at = datetime.now()
            progress.current_step = "迁移完成"
            
            logger.info(f"迁移任务 {task_id} 已完成")
            
        except Exception as e:
            progress.status = MigrationStatus.FAILED
            progress.error = str(e)
            progress.completed_at = datetime.now()
            logger.error(f"迁移任务 {task_id} 失败: {e}", exc_info=True)
        
        return progress
    
    def _translate_sql(self, task: MigrationTask, progress: MigrationProgress) -> None:
        """转换 SQL 语句"""
        source_db = connect(task.source_database, thread_count=1)
        target_db = connect(task.target_database, thread_count=1)
        
        source_dialect = DatabaseDialect.from_database(source_db)
        target_dialect = DatabaseDialect.from_database(target_db)
        
        translated_sqls = []
        
        # 转换 SQL 文件
        for sql_file in task.sql_files:
            try:
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql = f.read()
                    translated = self.sql_translator.translate(
                        sql, source_dialect, target_dialect
                    )
                    translated_sqls.append({
                        "file": sql_file,
                        "original": sql,
                        "translated": translated
                    })
            except Exception as e:
                logger.error(f"转换 SQL 文件 {sql_file} 时出错: {e}")
                raise
        
        # 转换 SQL 语句
        for sql in task.sql_statements:
            try:
                translated = self.sql_translator.translate(
                    sql, source_dialect, target_dialect
                )
                translated_sqls.append({
                    "original": sql,
                    "translated": translated
                })
            except Exception as e:
                logger.error(f"转换 SQL 语句时出错: {e}")
                raise
        
        progress.stats["translated_sqls"] = translated_sqls
        logger.info(f"已转换 {len(translated_sqls)} 条 SQL 语句")
    
    def _validate_migration(self, task: MigrationTask, progress: MigrationProgress) -> Dict[str, Any]:
        """验证迁移结果"""
        try:
            result = self.validator.validate(
                source_database=task.source_database,
                source_table=task.source_table,
                target_database=task.target_database,
                target_table=task.target_table,
                key_columns=task.key_columns,
                update_column=task.update_column,
                extra_columns=task.extra_columns,
                threshold=task.validation_threshold
            )
            
            progress.stats["validation"] = result
            
            if result["success"]:
                logger.info(f"迁移验证通过: {result.get('diff_count', 0)} 条差异")
            else:
                logger.warning(f"迁移验证失败: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"验证迁移时出错: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消迁移任务"""
        if task_id not in self.tasks:
            return False
        
        progress = self.progress[task_id]
        if progress.status in (MigrationStatus.COMPLETED, MigrationStatus.FAILED, MigrationStatus.CANCELLED):
            return False
        
        progress.status = MigrationStatus.CANCELLED
        progress.completed_at = datetime.now()
        progress.current_step = "已取消"
        
        logger.info(f"迁移任务 {task_id} 已取消")
        return True
    
    def list_tasks(self) -> List[MigrationTask]:
        """列出所有迁移任务"""
        return list(self.tasks.values())

