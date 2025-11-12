"""
DataMonitor CLI - 监控命令行接口
"""

import click
import json
import logging
from typing import Optional

from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator, MonitorScheduler, AlertManager, AlertChannel
from data_diff.utils import getLogger

logger = getLogger(__name__)


@click.group()
def monitor_cli():
    """数据监控命令行工具"""
    pass


@monitor_cli.command()
@click.option("--name", required=True, help="监控规则名称")
@click.option("--type", "monitor_type", type=click.Choice(["data_diff", "row_count", "schema_change"]), 
              default="data_diff", help="监控类型")
@click.option("--db1", required=True, help="数据库1连接字符串")
@click.option("--table1", required=True, help="表1名称")
@click.option("--db2", help="数据库2连接字符串（可选）")
@click.option("--table2", help="表2名称（可选）")
@click.option("--key-columns", multiple=True, default=["id"], help="主键列")
@click.option("--update-column", help="更新时间列")
@click.option("--extra-columns", multiple=True, help="额外比较的列")
@click.option("--threshold-type", type=click.Choice(["diff_count", "diff_percent", "row_count_diff"]), 
              help="阈值类型")
@click.option("--threshold-op", type=click.Choice([">", ">=", "<", "<=", "==", "!="]), 
              default=">", help="阈值操作符")
@click.option("--threshold-value", type=float, help="阈值数值")
@click.option("--schedule", help="Cron 表达式，如 '0 */6 * * *'")
@click.option("--description", help="规则描述")
def add_rule(name, monitor_type, db1, table1, db2, table2, key_columns, update_column,
             extra_columns, threshold_type, threshold_op, threshold_value, schedule, description):
    """添加监控规则"""
    monitor = DataMonitor()
    
    rule = MonitorRule(
        name=name,
        monitor_type=MonitorType(monitor_type),
        database1=db1,
        table1=table1,
        database2=db2,
        table2=table2,
        key_columns=tuple(key_columns),
        update_column=update_column,
        extra_columns=tuple(extra_columns),
        threshold_type=threshold_type,
        threshold_operator=RuleOperator(threshold_op),
        threshold_value=threshold_value,
        schedule=schedule,
        description=description
    )
    
    monitor.add_rule(rule)
    click.echo(f"✓ 已添加监控规则: {name}")


@monitor_cli.command()
@click.option("--name", required=True, help="监控规则名称")
def run(name):
    """执行监控规则"""
    monitor = DataMonitor()
    result = monitor.run_monitor(name)
    
    if result.success:
        click.echo(f"✓ 监控执行成功")
        click.echo(f"  差异数量: {result.diff_count}")
        click.echo(f"  差异百分比: {result.diff_percent:.2f}%")
        if result.triggered:
            click.echo(f"  ⚠️  已触发告警阈值")
    else:
        click.echo(f"✗ 监控执行失败: {result.error}")


@monitor_cli.command()
@click.option("--config", help="配置文件路径（TOML格式）")
def start(config):
    """启动监控调度器"""
    monitor = DataMonitor()
    alert_manager = AlertManager()
    
    # 如果提供了配置文件，加载规则
    if config:
        # TODO: 实现配置文件加载
        pass
    
    # 添加默认日志告警渠道
    alert_manager.add_channel(AlertChannel.LOG)
    
    scheduler = MonitorScheduler(monitor, alert_manager)
    scheduler.start()
    
    click.echo("监控调度器已启动，按 Ctrl+C 停止")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        click.echo("\n监控调度器已停止")


@monitor_cli.command()
@click.option("--name", help="规则名称（可选，不提供则列出所有）")
@click.option("--limit", default=10, help="结果数量限制")
@click.option("--json", "json_output", is_flag=True, help="JSON 格式输出")
def results(name, limit, json_output):
    """查看监控结果"""
    monitor = DataMonitor()
    results = monitor.get_results(name, limit)
    
    if json_output:
        output = [{
            "rule_name": r.rule_name,
            "timestamp": r.timestamp.isoformat(),
            "success": r.success,
            "diff_count": r.diff_count,
            "diff_percent": r.diff_percent,
            "triggered": r.triggered
        } for r in results]
        click.echo(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        for r in results:
            status = "✓" if r.success else "✗"
            triggered = " ⚠️" if r.triggered else ""
            click.echo(f"{status} {r.rule_name} - {r.timestamp} - "
                      f"差异: {r.diff_count} ({r.diff_percent:.2f}%){triggered}")


if __name__ == "__main__":
    monitor_cli()

