"""
SQLTranslator - SQL 转换器

支持不同数据库之间的 SQL 语法转换
"""

import re
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple

from data_diff.databases import Database
from data_diff.databases.mysql import MySQL
from data_diff.databases.postgresql import PostgreSQL
from data_diff.databases.snowflake import Snowflake
from data_diff.databases.clickhouse import Clickhouse
from data_diff.utils import getLogger

logger = getLogger(__name__)


class DatabaseDialect(Enum):
    """数据库方言"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SNOWFLAKE = "snowflake"
    CLICKHOUSE = "clickhouse"
    ORACLE = "oracle"
    MSSQL = "mssql"
    
    @classmethod
    def from_database(cls, db: Database) -> "DatabaseDialect":
        """从数据库实例获取方言"""
        if isinstance(db, MySQL):
            return cls.MYSQL
        elif isinstance(db, PostgreSQL):
            return cls.POSTGRESQL
        elif isinstance(db, Snowflake):
            return cls.SNOWFLAKE
        elif isinstance(db, Clickhouse):
            return cls.CLICKHOUSE
        else:
            # 尝试从数据库名称推断
            db_name = db.name.lower()
            for dialect in cls:
                if dialect.value in db_name:
                    return dialect
            raise ValueError(f"无法识别数据库方言: {type(db).__name__}")


class SQLTranslator:
    """SQL 转换器"""
    
    def __init__(self):
        self.conversion_rules: Dict[Tuple[DatabaseDialect, DatabaseDialect], Dict[str, str]] = {}
        self._init_conversion_rules()
    
    def _init_conversion_rules(self) -> None:
        """初始化转换规则"""
        # MySQL -> PostgreSQL
        self.conversion_rules[(DatabaseDialect.MYSQL, DatabaseDialect.POSTGRESQL)] = {
            r"`([^`]+)`": r'"\1"',  # 反引号转双引号
            r"LIMIT\s+(\d+)\s*,\s*(\d+)": r"LIMIT \2 OFFSET \1",  # LIMIT offset, count
            r"AUTO_INCREMENT": "SERIAL",  # 自增
            r"ENGINE\s*=\s*\w+": "",  # 移除 ENGINE
            r"DEFAULT\s+CURRENT_TIMESTAMP": "DEFAULT CURRENT_TIMESTAMP",
        }
        
        # PostgreSQL -> MySQL
        self.conversion_rules[(DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL)] = {
            r'"([^"]+)"': r"`\1`",  # 双引号转反引号
            r"LIMIT\s+(\d+)\s+OFFSET\s+(\d+)": r"LIMIT \2, \1",  # LIMIT count OFFSET offset
            r"SERIAL": "INT AUTO_INCREMENT",  # 自增
            r"::\w+": "",  # 移除类型转换
        }
        
        # MySQL -> Snowflake
        self.conversion_rules[(DatabaseDialect.MYSQL, DatabaseDialect.SNOWFLAKE)] = {
            r"`([^`]+)`": r'"\1"',
            r"LIMIT\s+(\d+)\s*,\s*(\d+)": r"LIMIT \2 OFFSET \1",
            r"AUTO_INCREMENT": "",
            r"ENGINE\s*=\s*\w+": "",
        }
        
        # PostgreSQL -> Snowflake
        self.conversion_rules[(DatabaseDialect.POSTGRESQL, DatabaseDialect.SNOWFLAKE)] = {
            r'"([^"]+)"': r'"\1"',
            r"::\w+": "",  # 移除类型转换
        }
    
    def translate(self, sql: str, source_dialect: DatabaseDialect, target_dialect: DatabaseDialect) -> str:
        """转换 SQL 语句"""
        if source_dialect == target_dialect:
            return sql
        
        rules = self.conversion_rules.get((source_dialect, target_dialect))
        if not rules:
            logger.warning(
                f"未找到从 {source_dialect.value} 到 {target_dialect.value} 的转换规则，"
                "返回原始 SQL"
            )
            return sql
        
        translated = sql
        for pattern, replacement in rules.items():
            translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)
        
        # 通用转换
        translated = self._apply_common_transformations(translated, source_dialect, target_dialect)
        
        return translated
    
    def _apply_common_transformations(self, sql: str, source: DatabaseDialect, target: DatabaseDialect) -> str:
        """应用通用转换规则"""
        # 数据类型转换
        type_mappings = self._get_type_mappings(source, target)
        for source_type, target_type in type_mappings.items():
            # 简单的类型替换（实际应该更智能）
            pattern = rf"\b{source_type}\b"
            sql = re.sub(pattern, target_type, sql, flags=re.IGNORECASE)
        
        # 函数名转换
        function_mappings = self._get_function_mappings(source, target)
        for source_func, target_func in function_mappings.items():
            pattern = rf"\b{source_func}\s*\("
            sql = re.sub(pattern, f"{target_func}(", sql, flags=re.IGNORECASE)
        
        return sql
    
    def _get_type_mappings(self, source: DatabaseDialect, target: DatabaseDialect) -> Dict[str, str]:
        """获取数据类型映射"""
        mappings = {
            (DatabaseDialect.MYSQL, DatabaseDialect.POSTGRESQL): {
                "TINYINT": "SMALLINT",
                "MEDIUMINT": "INTEGER",
                "LONGTEXT": "TEXT",
                "MEDIUMTEXT": "TEXT",
            },
            (DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL): {
                "SERIAL": "INT AUTO_INCREMENT",
                "BIGSERIAL": "BIGINT AUTO_INCREMENT",
                "TEXT": "LONGTEXT",
            },
            (DatabaseDialect.MYSQL, DatabaseDialect.SNOWFLAKE): {
                "TINYINT": "TINYINT",
                "MEDIUMINT": "INTEGER",
                "LONGTEXT": "VARCHAR",
            },
        }
        
        return mappings.get((source, target), {})
    
    def _get_function_mappings(self, source: DatabaseDialect, target: DatabaseDialect) -> Dict[str, str]:
        """获取函数名映射"""
        mappings = {
            (DatabaseDialect.MYSQL, DatabaseDialect.POSTGRESQL): {
                "NOW()": "CURRENT_TIMESTAMP",
                "IFNULL": "COALESCE",
            },
            (DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL): {
                "CURRENT_TIMESTAMP": "NOW()",
                "COALESCE": "IFNULL",
            },
        }
        
        return mappings.get((source, target), {})
    
    def translate_file(self, input_file: str, output_file: str, 
                      source_dialect: DatabaseDialect, target_dialect: DatabaseDialect) -> None:
        """转换 SQL 文件"""
        with open(input_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        translated = self.translate(sql, source_dialect, target_dialect)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated)
        
        logger.info(f"已转换 SQL 文件: {input_file} -> {output_file}")

