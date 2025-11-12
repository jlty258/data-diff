# 快速开始指南

## 第一步：先用起来

### 1. 安装依赖

```bash
# 进入项目目录
cd data-diff

# 安装基础依赖（如果还没有）
pip install -e .

# 安装新功能依赖
pip install croniter requests
```

### 2. 验证安装

```bash
# 运行快速测试脚本
python quick_start.py
```

如果看到 `✅ 所有测试通过！`，说明系统可以正常使用。

### 3. 最简单的测试（不需要真实数据库）

测试 SQL 转换功能（这是唯一不需要数据库连接的功能）：

```python
from data_diff.migration import SQLTranslator, DatabaseDialect

translator = SQLTranslator()

# MySQL SQL
mysql_sql = "SELECT * FROM `users` LIMIT 10, 20"

# 转换为 PostgreSQL
pg_sql = translator.translate(
    mysql_sql,
    DatabaseDialect.MYSQL,
    DatabaseDialect.POSTGRESQL
)

print(f"MySQL:   {mysql_sql}")
print(f"PostgreSQL: {pg_sql}")
```

### 4. 使用真实数据库测试

#### 测试数据监控

```python
from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator

# 创建监控器
monitor = DataMonitor()

# 创建规则（替换为你的真实数据库连接）
rule = MonitorRule(
    name="test_monitor",
    monitor_type=MonitorType.DATA_DIFF,
    database1="mysql://user:password@host:port/database",
    table1="table1",
    database2="mysql://user:password@host:port/database",
    table2="table2",
    key_columns=("id",),  # 替换为你的主键列
    threshold_type="diff_count",
    threshold_operator=RuleOperator.GT,
    threshold_value=0
)

# 添加规则
monitor.add_rule(rule)

# 执行一次监控
result = monitor.run_monitor("test_monitor")

# 查看结果
print(f"差异数量: {result.diff_count}")
print(f"差异百分比: {result.diff_percent:.2f}%")
print(f"表1行数: {result.row_count_table1}")
print(f"表2行数: {result.row_count_table2}")
```

#### 测试迁移验证

```python
from data_diff.migration import MigrationValidator

validator = MigrationValidator()

# 验证两个表的数据一致性（替换为你的真实连接）
result = validator.validate(
    source_database="postgresql://user:pass@host/db",
    source_table="source_table",
    target_database="mysql://user:pass@host/db",
    target_table="target_table",
    key_columns=("id",),  # 替换为你的主键列
    threshold=0.0  # 允许的差异百分比
)

if result["success"]:
    print("✅ 验证通过")
    print(f"差异数量: {result['diff_count']}")
else:
    print("❌ 验证失败")
    print(f"错误: {result.get('error')}")
```

## 第二步：缩减步骤（简化使用）

### 1. 创建配置文件

创建 `my_monitor_config.toml`：

```toml
[database]
# 定义数据库连接（可以复用）
prod = { driver = "mysql", host = "prod-host", database = "mydb", user = "user", password = "pass" }
staging = { driver = "mysql", host = "staging-host", database = "mydb", user = "user", password = "pass" }

[monitor.rules.simple_check]
name = "simple_check"
type = "data_diff"
database1 = "prod"
table1 = "orders"
database2 = "staging"
table2 = "orders"
key_columns = ["order_id"]
threshold_type = "diff_percent"
threshold_operator = ">"
threshold_value = 1.0
schedule = "0 */6 * * *"  # 每6小时
enabled = true
```

### 2. 一键启动脚本

创建 `start_monitor.py`：

```python
#!/usr/bin/env python3
"""一键启动监控"""

from data_diff.monitor import DataMonitor, MonitorScheduler, AlertManager, AlertChannel

# 加载配置（需要实现配置加载逻辑）
# 这里简化示例
monitor = DataMonitor()
alert_manager = AlertManager()
alert_manager.add_channel(AlertChannel.LOG)  # 先只用日志

# 添加你的规则
# monitor.add_rule(...)

# 启动调度器
scheduler = MonitorScheduler(monitor, alert_manager)
scheduler.start()

print("监控已启动，按 Ctrl+C 停止")

try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.stop()
    print("监控已停止")
```

### 3. 常用操作封装

创建 `my_tools.py`：

```python
"""常用工具函数"""

from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator
from data_diff.migration import MigrationValidator

def quick_check(db1, table1, db2, table2, key_col="id"):
    """快速检查两个表是否一致"""
    validator = MigrationValidator()
    result = validator.validate(
        source_database=db1,
        source_table=table1,
        target_database=db2,
        target_table=table2,
        key_columns=(key_col,),
        threshold=0.0
    )
    return result["success"], result.get("diff_count", 0)

def add_simple_monitor(name, db1, table1, db2, table2, key_col="id", threshold=1.0):
    """快速添加监控规则"""
    monitor = DataMonitor()
    rule = MonitorRule(
        name=name,
        monitor_type=MonitorType.DATA_DIFF,
        database1=db1,
        table1=table1,
        database2=db2,
        table2=table2,
        key_columns=(key_col,),
        threshold_type="diff_percent",
        threshold_operator=RuleOperator.GT,
        threshold_value=threshold
    )
    monitor.add_rule(rule)
    return monitor

# 使用示例
if __name__ == "__main__":
    # 快速检查
    success, diff = quick_check(
        "mysql://host/db", "table1",
        "mysql://host/db", "table2"
    )
    print(f"检查结果: {'一致' if success else '不一致'} (差异: {diff})")
```

## 第三步：对接各种系统

### 1. 集成到现有 Python 项目

```python
# 在你的项目中
from data_diff.monitor import DataMonitor, MonitorRule, MonitorType

class MyDataService:
    def __init__(self):
        self.monitor = DataMonitor()
        self._setup_monitors()
    
    def _setup_monitors(self):
        # 添加监控规则
        rule = MonitorRule(...)
        self.monitor.add_rule(rule)
    
    def check_data_quality(self):
        # 执行监控
        results = []
        for rule in self.monitor.list_rules():
            result = self.monitor.run_monitor(rule.name)
            results.append(result)
        return results
```

### 2. 通过 API 暴露（Flask 示例）

```python
from flask import Flask, jsonify
from data_diff.monitor import DataMonitor

app = Flask(__name__)
monitor = DataMonitor()

@app.route('/api/monitor/run/<rule_name>', methods=['POST'])
def run_monitor(rule_name):
    result = monitor.run_monitor(rule_name)
    return jsonify({
        "success": result.success,
        "diff_count": result.diff_count,
        "diff_percent": result.diff_percent,
        "triggered": result.triggered
    })

@app.route('/api/monitor/results/<rule_name>')
def get_results(rule_name):
    results = monitor.get_results(rule_name, limit=10)
    return jsonify([{
        "timestamp": r.timestamp.isoformat(),
        "diff_count": r.diff_count,
        "diff_percent": r.diff_percent
    } for r in results])
```

### 3. 集成到 CI/CD

创建 `.github/workflows/data-quality-check.yml`：

```yaml
name: Data Quality Check

on:
  schedule:
    - cron: '0 */6 * * *'  # 每6小时
  workflow_dispatch:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -e . croniter requests
      - run: |
          python -c "
          from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator
          monitor = DataMonitor()
          rule = MonitorRule(
              name='ci_check',
              monitor_type=MonitorType.DATA_DIFF,
              database1='${{ secrets.PROD_DB }}',
              table1='orders',
              database2='${{ secrets.STAGING_DB }}',
              table2='orders',
              key_columns=('id',),
              threshold_type='diff_percent',
              threshold_operator=RuleOperator.GT,
              threshold_value=1.0
          )
          monitor.add_rule(rule)
          result = monitor.run_monitor('ci_check')
          if result.triggered:
              exit(1)
          "
```

### 4. 对接告警系统

```python
from data_diff.monitor import AlertManager, AlertChannel

# 对接你的告警系统
alert_manager = AlertManager()

# 邮件告警
alert_manager.add_channel(AlertChannel.EMAIL, config={
    "smtp_host": "your-smtp.com",
    "smtp_port": 587,
    "from_email": "alerts@yourcompany.com",
    "to_emails": ["team@yourcompany.com"]
})

# Webhook 告警（对接你的监控系统）
alert_manager.add_channel(AlertChannel.WEBHOOK, config={
    "url": "https://your-monitoring-system.com/webhook",
    "headers": {"Authorization": "Bearer YOUR_TOKEN"}
})
```

## 使用建议

### 阶段 1：先用起来（当前阶段）
- ✅ 运行 `quick_start.py` 验证安装
- ✅ 测试 SQL 转换功能（不需要数据库）
- ✅ 用真实数据库测试一次监控
- ✅ 用真实数据库测试一次迁移验证

### 阶段 2：缩减步骤
- 📝 创建配置文件，简化规则管理
- 📝 封装常用操作为函数
- 📝 创建一键启动脚本

### 阶段 3：对接系统
- 🔌 集成到现有项目
- 🔌 通过 API 暴露功能
- 🔌 集成到 CI/CD
- 🔌 对接告警系统

## 常见问题

**Q: 如何测试而不连接真实数据库？**
A: 可以只测试 SQL 转换功能，或者使用 Docker 启动测试数据库。

**Q: 如何查看监控历史？**
A: 使用 `monitor.get_results(rule_name)` 获取历史结果。

**Q: 如何调试问题？**
A: 启用 debug 日志：`import logging; logging.basicConfig(level=logging.DEBUG)`

## 下一步

1. 运行 `python quick_start.py` 验证安装
2. 根据你的实际数据库，修改示例代码中的连接信息
3. 运行一次完整的监控测试
4. 根据实际需求调整配置

