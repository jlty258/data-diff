# DataMonitor 和 Migration Agent 实现总结

## 概述

在 data-diff 项目基础上，我们实现了两个核心功能模块：

1. **DataMonitor** - 数据监控模块
2. **Migration Agent** - 数据迁移代理模块

## 项目结构

```
data-diff/
├── data_diff/
│   ├── monitor/              # 数据监控模块
│   │   ├── __init__.py
│   │   ├── monitor.py        # 核心监控器
│   │   ├── scheduler.py      # 调度器
│   │   └── alert.py          # 告警管理器
│   ├── migration/            # 迁移代理模块
│   │   ├── __init__.py
│   │   ├── agent.py          # 迁移代理核心
│   │   ├── sql_translator.py # SQL 转换器
│   │   └── validator.py      # 迁移验证器
│   ├── monitor_cli.py        # 监控命令行接口
│   └── migration_cli.py      # 迁移命令行接口
├── examples/
│   ├── monitor_config.toml   # 监控配置示例
│   └── migration_example.py  # 使用示例
└── MONITOR_AND_MIGRATION.md  # 详细使用文档
```

## 功能特性

### DataMonitor

✅ **监控类型**
- 数据差异监控（DATA_DIFF）
- 行数监控（ROW_COUNT）
- 模式变更监控（SCHEMA_CHANGE）

✅ **调度功能**
- 基于 cron 表达式的定时执行
- 支持多规则并发调度
- 手动触发执行

✅ **告警功能**
- 日志告警（默认）
- 邮件告警
- Webhook 告警
- Slack 告警
- 钉钉告警

✅ **阈值规则**
- 差异数量阈值
- 差异百分比阈值
- 行数差异阈值
- 支持多种比较操作符（>, >=, <, <=, ==, !=）

### Migration Agent

✅ **SQL 转换**
- MySQL ↔ PostgreSQL
- MySQL ↔ Snowflake
- PostgreSQL ↔ Snowflake
- 可扩展的转换规则

✅ **迁移验证**
- 自动验证迁移后的数据一致性
- 支持差异阈值配置
- 批量验证支持

✅ **进度跟踪**
- 实时跟踪迁移进度
- 状态管理（PENDING, RUNNING, VALIDATING, COMPLETED, FAILED, CANCELLED）
- 错误处理和报告

## 快速开始

### 安装依赖

```bash
pip install croniter requests
```

### 使用 DataMonitor

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

### 使用 Migration Agent

```python
from data_diff.migration import MigrationAgent, MigrationTask

agent = MigrationAgent()

task = MigrationTask(
    task_id="migration_001",
    source_database="postgresql://source/db",
    target_database="mysql://target/db",
    source_table="orders",
    target_table="orders",
    key_columns=("order_id",),
    validate_after_migration=True
)

agent.create_task(task)
progress = agent.execute_migration("migration_001")
```

## 命令行工具

### 监控命令

```bash
# 添加监控规则
python -m data_diff.monitor_cli add-rule --name my_monitor ...

# 执行监控
python -m data_diff.monitor_cli run --name my_monitor

# 查看结果
python -m data_diff.monitor_cli results --name my_monitor

# 启动调度器
python -m data_diff.monitor_cli start
```

### 迁移命令

```bash
# 创建迁移任务
python -m data_diff.migration_cli create --source-db ... --target-db ...

# 执行迁移
python -m data_diff.migration_cli execute --task-id <task_id>

# 查看状态
python -m data_diff.migration_cli status --task-id <task_id>

# 验证迁移
python -m data_diff.migration_cli validate --source-db ... --target-db ...
```

## 配置示例

查看 `examples/monitor_config.toml` 了解完整的配置格式。

## 注意事项

1. **依赖项**：需要安装 `croniter` 和 `requests`
2. **数据库连接**：确保有足够的数据库权限
3. **性能**：监控规则会定期执行，注意对数据库的影响
4. **SQL 转换**：复杂 SQL 可能需要手动调整

## 扩展性

两个模块都设计为可扩展的：

- **监控类型**：可以轻松添加新的监控类型
- **告警渠道**：可以添加新的告警渠道
- **SQL 转换**：可以添加新的数据库方言转换规则
- **验证规则**：可以添加自定义验证逻辑

## 文档

详细使用文档请参考 `MONITOR_AND_MIGRATION.md`。

