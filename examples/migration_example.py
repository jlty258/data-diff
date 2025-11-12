"""
Migration Agent 使用示例
"""

from data_diff.migration import MigrationAgent, MigrationTask
from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator, MonitorScheduler, AlertManager, AlertChannel


def example_migration():
    """迁移示例"""
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
    
    agent.create_task(task)
    
    # 执行迁移
    progress = agent.execute_migration("migration_001")
    
    print(f"迁移状态: {progress.status.value}")
    print(f"进度: {progress.progress_percent:.1f}%")
    if progress.error:
        print(f"错误: {progress.error}")


def example_monitor():
    """监控示例"""
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


if __name__ == "__main__":
    print("=== 迁移示例 ===")
    example_migration()
    
    print("\n=== 监控示例 ===")
    example_monitor()

