# Data-Diff Enhanced

基于 [datafold/data-diff](https://github.com/datafold/data-diff) 的扩展版本，添加了数据监控和迁移自动化功能。

## 🎯 新增功能

### 1. DataMonitor - 数据质量监控

- ✅ 多种监控类型（数据差异、行数、模式变更）
- ✅ 灵活的阈值规则
- ✅ 基于 cron 的定时调度
- ✅ 多渠道告警（日志、邮件、Webhook、Slack、钉钉）
- ✅ 历史记录保存

### 2. Migration Agent - 数据迁移代理

- ✅ SQL 自动转换（MySQL ↔ PostgreSQL ↔ Snowflake）
- ✅ 迁移验证（自动验证数据一致性）
- ✅ 进度跟踪（实时状态和进度）
- ✅ 任务管理

## 📦 安装

```bash
# 安装基础依赖
pip install -e .

# 安装新功能依赖
pip install croniter requests
```

## 🚀 快速开始

```bash
# 验证安装
python quick_start.py

# 测试 SQL 转换（不需要数据库）
python test_sql_translation.py
```

## 📚 文档

- [快速开始指南](GETTING_STARTED.md)
- [详细使用文档](MONITOR_AND_MIGRATION.md)
- [实现总结](README_MONITOR_MIGRATION.md)

## 💡 使用示例

### 数据监控

```python
from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator

monitor = DataMonitor()
rule = MonitorRule(
    name="my_monitor",
    monitor_type=MonitorType.DATA_DIFF,
    database1="mysql://user:pass@host/db",
    table1="table1",
    database2="mysql://user:pass@host/db",
    table2="table2",
    key_columns=("id",),
    threshold_type="diff_percent",
    threshold_operator=RuleOperator.GT,
    threshold_value=1.0
)
monitor.add_rule(rule)
result = monitor.run_monitor("my_monitor")
```

### 迁移验证

```python
from data_diff.migration import MigrationValidator

validator = MigrationValidator()
result = validator.validate(
    source_database="postgresql://source/db",
    source_table="orders",
    target_database="mysql://target/db",
    target_table="orders",
    key_columns=("order_id",)
)
```

## 📝 项目结构

```
data-diff/
├── data_diff/
│   ├── monitor/          # 数据监控模块
│   ├── migration/        # 迁移代理模块
│   ├── monitor_cli.py    # 监控命令行工具
│   └── migration_cli.py  # 迁移命令行工具
├── examples/              # 使用示例
├── quick_start.py         # 快速验证脚本
└── test_sql_translation.py # SQL 转换测试
```

## 🙏 致谢

- 原始项目：[datafold/data-diff](https://github.com/datafold/data-diff)
- 许可证：MIT

## 📄 许可证

本项目基于 datafold/data-diff，遵循 MIT 许可证。

