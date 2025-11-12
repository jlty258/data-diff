# DataMonitor 和 Migration Agent 使用指南

本文档介绍如何在 data-diff 基础上使用 DataMonitor（数据监控）和 Migration Agent（迁移代理）功能。

## 目录

- [DataMonitor - 数据监控](#datamonitor---数据监控)
- [Migration Agent - 迁移代理](#migration-agent---迁移代理)
- [安装依赖](#安装依赖)
- [快速开始](#快速开始)

## DataMonitor - 数据监控

DataMonitor 提供数据质量监控、告警和调度功能，帮助您持续监控数据一致性。

### 功能特性

- ✅ **多种监控类型**：数据差异、行数监控、模式变更监控
- ✅ **灵活的阈值规则**：支持差异数量、差异百分比、行数差异等阈值
- ✅ **定时调度**：基于 cron 表达式的定时执行
- ✅ **多渠道告警**：支持日志、邮件、Webhook、Slack、钉钉等告警渠道
- ✅ **历史记录**：保存监控结果和告警历史

### 使用示例

#### 1. Python API 使用

```python
from data_diff.monitor import (
    DataMonitor, MonitorRule, MonitorType, RuleOperator,
    MonitorScheduler, AlertManager, AlertChannel
)

# 创建监控器
monitor = DataMonitor()

# 创建监控规则
rule = MonitorRule(
    name="orders_monitor",
    monitor_type=MonitorType.DATA_DIFF,
    database1="postgresql://user:pass@prod/db",
    table1="orders",
    database2="postgresql://user:pass@staging/db",
    table2="orders",
    key_columns=("order_id",),
    update_column="updated_at",
    extra_columns=("amount", "status"),
    threshold_type="diff_percent",
    threshold_operator=RuleOperator.GT,
    threshold_value=1.0,  # 差异超过 1% 时告警
    schedule="0 */6 * * *",  # 每6小时执行一次
    description="监控生产环境和预发布环境的订单表差异"
)

# 添加规则
monitor.add_rule(rule)

# 配置告警
alert_manager = AlertManager()
alert_manager.add_channel(AlertChannel.LOG)
alert_manager.add_channel(
    AlertChannel.EMAIL,
    config={
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "alerts@example.com",
        "smtp_password": "password",
        "from_email": "data-monitor@example.com",
        "to_emails": ["team@example.com"]
    }
)

# 启动调度器
scheduler = MonitorScheduler(monitor, alert_manager)
scheduler.start()

# 手动执行一次
result = monitor.run_monitor("orders_monitor")
print(f"差异数量: {result.diff_count}")
print(f"差异百分比: {result.diff_percent:.2f}%")
print(f"是否触发告警: {result.triggered}")
```

#### 2. 命令行使用

```bash
# 添加监控规则
python -m data_diff.monitor_cli add-rule \
  --name orders_monitor \
  --type data_diff \
  --db1 postgresql://user:pass@prod/db \
  --table1 orders \
  --db2 postgresql://user:pass@staging/db \
  --table2 orders \
  --key-columns order_id \
  --update-column updated_at \
  --extra-columns amount status \
  --threshold-type diff_percent \
  --threshold-op ">" \
  --threshold-value 1.0 \
  --schedule "0 */6 * * *"

# 执行监控
python -m data_diff.monitor_cli run --name orders_monitor

# 查看结果
python -m data_diff.monitor_cli results --name orders_monitor

# 启动调度器
python -m data_diff.monitor_cli start
```

#### 3. 配置文件使用

创建 `monitor_config.toml`：

```toml
[database]
prod = { driver = "postgresql", host = "prod-db.example.com", database = "mydb" }
staging = { driver = "postgresql", host = "staging-db.example.com", database = "mydb" }

[monitor.rules.orders_diff]
name = "orders_diff"
type = "data_diff"
database1 = "prod"
table1 = "orders"
database2 = "staging"
table2 = "orders"
key_columns = ["order_id"]
threshold_type = "diff_percent"
threshold_operator = ">"
threshold_value = 1.0
schedule = "0 */6 * * *"
enabled = true
```

### 监控类型

1. **DATA_DIFF**：数据差异监控，比较两个表的数据差异
2. **ROW_COUNT**：行数监控，监控表的行数变化
3. **SCHEMA_CHANGE**：模式变更监控，检测表结构变化

### 告警渠道

- **LOG**：日志告警（默认）
- **EMAIL**：邮件告警
- **WEBHOOK**：HTTP Webhook 告警
- **SLACK**：Slack 告警
- **DINGTALK**：钉钉告警

## Migration Agent - 迁移代理

Migration Agent 提供数据迁移自动化功能，包括 SQL 转换、迁移验证和进度跟踪。

### 功能特性

- ✅ **SQL 转换**：自动转换不同数据库之间的 SQL 语法
- ✅ **迁移验证**：验证迁移后的数据一致性
- ✅ **进度跟踪**：实时跟踪迁移进度
- ✅ **批量验证**：支持批量验证多个迁移任务

### 支持的数据库转换

- MySQL ↔ PostgreSQL
- MySQL ↔ Snowflake
- PostgreSQL ↔ Snowflake
- 更多转换规则可扩展

### 使用示例

#### 1. Python API 使用

```python
from data_diff.migration import MigrationAgent, MigrationTask

# 创建迁移代理
agent = MigrationAgent()

# 创建迁移任务
task = MigrationTask(
    task_id="migration_001",
    source_database="postgresql://user:pass@source-host/db",
    target_database="mysql://user:pass@target-host/db",
    source_table="orders",
    target_table="orders",
    key_columns=("order_id",),
    update_column="updated_at",
    extra_columns=("amount", "status", "created_at"),
    sql_files=["schema.sql", "migrations.sql"],
    validate_after_migration=True,
    validation_threshold=0.1,  # 允许 0.1% 的差异
    description="迁移订单表从 PostgreSQL 到 MySQL"
)

# 创建任务
agent.create_task(task)

# 执行迁移
progress = agent.execute_migration("migration_001")

print(f"迁移状态: {progress.status.value}")
print(f"进度: {progress.progress_percent:.1f}%")
```

#### 2. 命令行使用

```bash
# 创建迁移任务
python -m data_diff.migration_cli create \
  --source-db postgresql://user:pass@source/db \
  --source-table orders \
  --target-db mysql://user:pass@target/db \
  --target-table orders \
  --key-columns order_id \
  --sql-file schema.sql \
  --validate \
  --threshold 0.1

# 执行迁移
python -m data_diff.migration_cli execute --task-id <task_id>

# 查看状态
python -m data_diff.migration_cli status --task-id <task_id>

# 验证迁移结果
python -m data_diff.migration_cli validate \
  --source-db postgresql://user:pass@source/db \
  --source-table orders \
  --target-db mysql://user:pass@target/db \
  --target-table orders \
  --key-columns order_id \
  --threshold 0.1
```

#### 3. SQL 转换示例

```python
from data_diff.migration import SQLTranslator, DatabaseDialect

translator = SQLTranslator()

# MySQL SQL
mysql_sql = """
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    `order_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10, 2)
) ENGINE=InnoDB;
"""

# 转换为 PostgreSQL SQL
pg_sql = translator.translate(
    mysql_sql,
    DatabaseDialect.MYSQL,
    DatabaseDialect.POSTGRESQL
)

print(pg_sql)
# 输出：
# CREATE TABLE orders (
#     id SERIAL PRIMARY KEY,
#     "order_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     amount DECIMAL(10, 2)
# );
```

## 安装依赖

确保安装以下依赖：

```bash
pip install croniter requests
```

或者使用 poetry：

```bash
poetry add croniter requests
```

## 快速开始

### 1. 数据监控

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
    threshold_type="diff_count",
    threshold_operator=RuleOperator.GT,
    threshold_value=10
)

monitor.add_rule(rule)
result = monitor.run_monitor("my_monitor")
print(f"差异: {result.diff_count}")
```

### 2. 迁移验证

```python
from data_diff.migration import MigrationValidator

validator = MigrationValidator()

result = validator.validate(
    source_database="postgresql://source/db",
    source_table="orders",
    target_database="mysql://target/db",
    target_table="orders",
    key_columns=("order_id",),
    threshold=0.0
)

if result["success"]:
    print("✓ 迁移验证通过")
else:
    print(f"✗ 验证失败: {result['error']}")
```

## 更多信息

- 查看 `examples/` 目录下的示例代码
- 查看 `examples/monitor_config.toml` 了解配置文件格式
- 查看 `examples/migration_example.py` 了解完整使用示例

## 注意事项

1. **性能考虑**：监控规则会定期执行，注意对数据库的影响
2. **权限要求**：确保数据库连接有足够的权限执行查询
3. **告警配置**：生产环境建议配置多个告警渠道
4. **SQL 转换**：SQL 转换器基于规则，复杂 SQL 可能需要手动调整
5. **迁移验证**：大表验证可能需要较长时间，建议设置合理的阈值

