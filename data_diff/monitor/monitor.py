"""
DataMonitor - 核心监控器实现
"""

import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from data_diff import connect_to_table, diff_tables, Algorithm
from data_diff.diff_tables import DiffResultWrapper
from data_diff.utils import getLogger

logger = getLogger(__name__)


class MonitorType(Enum):
    """监控类型"""
    DATA_DIFF = "data_diff"  # 数据差异监控
    ROW_COUNT = "row_count"  # 行数监控
    DATA_QUALITY = "data_quality"  # 数据质量监控
    SCHEMA_CHANGE = "schema_change"  # 模式变更监控


class RuleOperator(Enum):
    """规则操作符"""
    GT = ">"  # 大于
    GTE = ">="  # 大于等于
    LT = "<"  # 小于
    LTE = "<="  # 小于等于
    EQ = "=="  # 等于
    NE = "!="  # 不等于
    BETWEEN = "between"  # 在范围内


@dataclass
class MonitorRule:
    """监控规则"""
    name: str
    monitor_type: MonitorType
    database1: str
    table1: str
    database2: Optional[str] = None
    table2: Optional[str] = None
    key_columns: Tuple[str, ...] = ("id",)
    update_column: Optional[str] = None
    extra_columns: Tuple[str, ...] = ()
    
    # 阈值规则
    threshold_type: Optional[str] = None  # "diff_count", "diff_percent", "row_count_diff"
    threshold_operator: RuleOperator = RuleOperator.GT
    threshold_value: Optional[float] = None
    
    # 调度配置
    schedule: Optional[str] = None  # cron 表达式，如 "0 */6 * * *" 表示每6小时
    enabled: bool = True
    
    # 元数据
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitorResult:
    """监控结果"""
    rule_name: str
    timestamp: datetime
    success: bool
    diff_count: int = 0
    diff_percent: float = 0.0
    row_count_table1: int = 0
    row_count_table2: int = 0
    stats: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_seconds: float = 0.0
    triggered: bool = False  # 是否触发告警阈值


class DataMonitor:
    """数据监控器"""
    
    def __init__(self):
        self.rules: Dict[str, MonitorRule] = {}
        self.results: List[MonitorResult] = []
    
    def add_rule(self, rule: MonitorRule) -> None:
        """添加监控规则"""
        if rule.name in self.rules:
            logger.warning(f"规则 '{rule.name}' 已存在，将被覆盖")
        self.rules[rule.name] = rule
        logger.info(f"添加监控规则: {rule.name} ({rule.monitor_type.value})")
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除监控规则"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"移除监控规则: {rule_name}")
            return True
        return False
    
    def run_monitor(self, rule_name: str) -> MonitorResult:
        """执行单个监控规则"""
        if rule_name not in self.rules:
            raise ValueError(f"监控规则 '{rule_name}' 不存在")
        
        rule = self.rules[rule_name]
        if not rule.enabled:
            logger.info(f"监控规则 '{rule_name}' 已禁用，跳过执行")
            return MonitorResult(
                rule_name=rule_name,
                timestamp=datetime.now(),
                success=True,
                triggered=False
            )
        
        start_time = time.monotonic()
        result = None
        
        try:
            if rule.monitor_type == MonitorType.DATA_DIFF:
                result = self._run_data_diff_monitor(rule)
            elif rule.monitor_type == MonitorType.ROW_COUNT:
                result = self._run_row_count_monitor(rule)
            elif rule.monitor_type == MonitorType.SCHEMA_CHANGE:
                result = self._run_schema_change_monitor(rule)
            else:
                raise ValueError(f"不支持的监控类型: {rule.monitor_type}")
            
            # 检查是否触发阈值
            result.triggered = self._check_threshold(rule, result)
            
        except Exception as e:
            logger.error(f"执行监控规则 '{rule_name}' 时出错: {e}", exc_info=True)
            result = MonitorResult(
                rule_name=rule_name,
                timestamp=datetime.now(),
                success=False,
                error=str(e),
                duration_seconds=time.monotonic() - start_time
            )
        
        if result:
            result.duration_seconds = time.monotonic() - start_time
            self.results.append(result)
            # 只保留最近1000条结果
            if len(self.results) > 1000:
                self.results = self.results[-1000:]
        
        return result
    
    def _run_data_diff_monitor(self, rule: MonitorRule) -> MonitorResult:
        """执行数据差异监控"""
        logger.info(f"执行数据差异监控: {rule.name}")
        
        table1 = connect_to_table(
            rule.database1,
            rule.table1,
            rule.key_columns,
            update_column=rule.update_column,
            extra_columns=rule.extra_columns
        )
        
        if rule.database2 and rule.table2:
            # 跨数据库比较
            table2 = connect_to_table(
                rule.database2,
                rule.table2,
                rule.key_columns,
                update_column=rule.update_column,
                extra_columns=rule.extra_columns
            )
            algorithm = Algorithm.HASHDIFF
        else:
            # 同数据库比较
            table2 = connect_to_table(
                rule.database1,
                rule.table2 or rule.table1,
                rule.key_columns,
                update_column=rule.update_column,
                extra_columns=rule.extra_columns
            )
            algorithm = Algorithm.JOINDIFF
        
        diff_result: DiffResultWrapper = diff_tables(
            table1,
            table2,
            algorithm=algorithm,
            extra_columns=rule.extra_columns
        )
        
        # 获取统计信息
        stats = diff_result.get_stats_dict()
        
        diff_count = stats.get("total", 0)
        row_count1 = stats.get("rows_A", 0)
        row_count2 = stats.get("rows_B", 0)
        
        # 计算差异百分比
        max_rows = max(row_count1, row_count2) if (row_count1 or row_count2) else 1
        diff_percent = (diff_count / max_rows * 100) if max_rows > 0 else 0.0
        
        return MonitorResult(
            rule_name=rule.name,
            timestamp=datetime.now(),
            success=True,
            diff_count=diff_count,
            diff_percent=diff_percent,
            row_count_table1=row_count1,
            row_count_table2=row_count2,
            stats=stats
        )
    
    def _run_row_count_monitor(self, rule: MonitorRule) -> MonitorResult:
        """执行行数监控"""
        logger.info(f"执行行数监控: {rule.name}")
        
        table1 = connect_to_table(rule.database1, rule.table1, rule.key_columns)
        row_count1 = table1.count()
        
        row_count2 = 0
        if rule.database2 and rule.table2:
            table2 = connect_to_table(rule.database2, rule.table2, rule.key_columns)
            row_count2 = table2.count()
        
        diff_count = abs(row_count1 - row_count2)
        diff_percent = (diff_count / max(row_count1, row_count2) * 100) if max(row_count1, row_count2) > 0 else 0.0
        
        return MonitorResult(
            rule_name=rule.name,
            timestamp=datetime.now(),
            success=True,
            diff_count=diff_count,
            diff_percent=diff_percent,
            row_count_table1=row_count1,
            row_count_table2=row_count2
        )
    
    def _run_schema_change_monitor(self, rule: MonitorRule) -> MonitorResult:
        """执行模式变更监控"""
        logger.info(f"执行模式变更监控: {rule.name}")
        
        table1 = connect_to_table(rule.database1, rule.table1, rule.key_columns)
        schema1 = table1.get_schema()
        
        schema2 = {}
        if rule.database2 and rule.table2:
            table2 = connect_to_table(rule.database2, rule.table2, rule.key_columns)
            schema2 = table2.get_schema()
        elif rule.table2:
            table2 = connect_to_table(rule.database1, rule.table2, rule.key_columns)
            schema2 = table2.get_schema()
        
        # 比较模式差异
        cols1 = set(schema1.keys())
        cols2 = set(schema2.keys())
        
        added_cols = cols2 - cols1
        removed_cols = cols1 - cols2
        common_cols = cols1 & cols2
        
        type_changes = []
        for col in common_cols:
            if schema1[col].type != schema2[col].type:
                type_changes.append(col)
        
        diff_count = len(added_cols) + len(removed_cols) + len(type_changes)
        
        return MonitorResult(
            rule_name=rule.name,
            timestamp=datetime.now(),
            success=True,
            diff_count=diff_count,
            stats={
                "added_columns": list(added_cols),
                "removed_columns": list(removed_cols),
                "type_changes": type_changes
            }
        )
    
    def _check_threshold(self, rule: MonitorRule, result: MonitorResult) -> bool:
        """检查是否触发阈值"""
        if not rule.threshold_type or rule.threshold_value is None:
            return False
        
        value_to_check = None
        if rule.threshold_type == "diff_count":
            value_to_check = result.diff_count
        elif rule.threshold_type == "diff_percent":
            value_to_check = result.diff_percent
        elif rule.threshold_type == "row_count_diff":
            value_to_check = abs(result.row_count_table1 - result.row_count_table2)
        
        if value_to_check is None:
            return False
        
        op = rule.threshold_operator
        threshold = rule.threshold_value
        
        if op == RuleOperator.GT:
            return value_to_check > threshold
        elif op == RuleOperator.GTE:
            return value_to_check >= threshold
        elif op == RuleOperator.LT:
            return value_to_check < threshold
        elif op == RuleOperator.LTE:
            return value_to_check <= threshold
        elif op == RuleOperator.EQ:
            return abs(value_to_check - threshold) < 0.0001
        elif op == RuleOperator.NE:
            return abs(value_to_check - threshold) >= 0.0001
        
        return False
    
    def get_results(self, rule_name: Optional[str] = None, limit: int = 100) -> List[MonitorResult]:
        """获取监控结果"""
        results = self.results
        if rule_name:
            results = [r for r in results if r.rule_name == rule_name]
        return results[-limit:]
    
    def get_rule(self, rule_name: str) -> Optional[MonitorRule]:
        """获取监控规则"""
        return self.rules.get(rule_name)
    
    def list_rules(self) -> List[MonitorRule]:
        """列出所有监控规则"""
        return list(self.rules.values())

