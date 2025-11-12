"""
MigrationValidator - 迁移验证器

验证数据迁移后的数据一致性
"""

import logging
from typing import Dict, Any, Optional, Tuple

from data_diff import connect_to_table, diff_tables, Algorithm
from data_diff.diff_tables import DiffResultWrapper
from data_diff.utils import getLogger

logger = getLogger(__name__)


class MigrationValidator:
    """迁移验证器"""
    
    def validate(self,
                 source_database: str,
                 source_table: str,
                 target_database: str,
                 target_table: str,
                 key_columns: Tuple[str, ...] = ("id",),
                 update_column: Optional[str] = None,
                 extra_columns: Tuple[str, ...] = (),
                 threshold: float = 0.0) -> Dict[str, Any]:
        """
        验证迁移结果
        
        Args:
            source_database: 源数据库连接字符串
            source_table: 源表名
            target_database: 目标数据库连接字符串
            target_table: 目标表名
            key_columns: 主键列
            update_column: 更新时间列
            extra_columns: 额外比较的列
            threshold: 允许的差异百分比阈值（0.0 表示不允许任何差异）
        
        Returns:
            验证结果字典，包含 success, diff_count, diff_percent, stats 等
        """
        logger.info(f"开始验证迁移: {source_table} -> {target_table}")
        
        try:
            # 连接到两个表
            table1 = connect_to_table(
                source_database,
                source_table,
                key_columns,
                update_column=update_column,
                extra_columns=extra_columns
            )
            
            table2 = connect_to_table(
                target_database,
                target_table,
                key_columns,
                update_column=update_column,
                extra_columns=extra_columns
            )
            
            # 执行差异比较
            diff_result: DiffResultWrapper = diff_tables(
                table1,
                table2,
                algorithm=Algorithm.HASHDIFF,  # 跨数据库使用 hashdiff
                extra_columns=extra_columns
            )
            
            # 获取统计信息
            stats = diff_result.get_stats_dict()
            
            diff_count = stats.get("total", 0)
            row_count1 = stats.get("rows_A", 0)
            row_count2 = stats.get("rows_B", 0)
            
            # 计算差异百分比
            max_rows = max(row_count1, row_count2) if (row_count1 or row_count2) else 1
            diff_percent = (diff_count / max_rows * 100) if max_rows > 0 else 0.0
            
            # 判断是否通过验证
            success = diff_percent <= threshold
            
            result = {
                "success": success,
                "diff_count": diff_count,
                "diff_percent": diff_percent,
                "row_count_source": row_count1,
                "row_count_target": row_count2,
                "threshold": threshold,
                "stats": stats
            }
            
            if not success:
                result["error"] = (
                    f"差异百分比 {diff_percent:.2f}% 超过阈值 {threshold}% "
                    f"(差异数量: {diff_count})"
                )
            
            logger.info(
                f"验证完成: {'通过' if success else '失败'} "
                f"(差异: {diff_count}, 百分比: {diff_percent:.2f}%)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"验证迁移时出错: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_batch(self, validations: list) -> Dict[str, Any]:
        """
        批量验证多个迁移任务
        
        Args:
            validations: 验证配置列表，每个元素包含 validate() 方法的参数
        
        Returns:
            批量验证结果
        """
        results = []
        total = len(validations)
        passed = 0
        
        for i, validation_config in enumerate(validations, 1):
            logger.info(f"验证进度: {i}/{total}")
            result = self.validate(**validation_config)
            results.append(result)
            if result["success"]:
                passed += 1
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "results": results
        }

