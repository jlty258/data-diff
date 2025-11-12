"""
Migration Agent CLI - 迁移代理命令行接口
"""

import click
import json
import uuid
from typing import Optional

from data_diff.migration import MigrationAgent, MigrationTask, MigrationStatus
from data_diff.utils import getLogger

logger = getLogger(__name__)


@click.group()
def migration_cli():
    """数据迁移代理命令行工具"""
    pass


@migration_cli.command()
@click.option("--source-db", required=True, help="源数据库连接字符串")
@click.option("--source-table", required=True, help="源表名")
@click.option("--target-db", required=True, help="目标数据库连接字符串")
@click.option("--target-table", required=True, help="目标表名")
@click.option("--key-columns", multiple=True, default=["id"], help="主键列")
@click.option("--update-column", help="更新时间列")
@click.option("--extra-columns", multiple=True, help="额外比较的列")
@click.option("--sql-file", multiple=True, help="需要转换的 SQL 文件")
@click.option("--sql-statement", multiple=True, help="需要转换的 SQL 语句")
@click.option("--validate/--no-validate", default=True, help="是否验证迁移结果")
@click.option("--threshold", type=float, default=0.0, help="验证阈值（差异百分比）")
@click.option("--description", help="任务描述")
def create(source_db, source_table, target_db, target_table, key_columns, update_column,
          extra_columns, sql_file, sql_statement, validate, threshold, description):
    """创建迁移任务"""
    agent = MigrationAgent()
    
    task = MigrationTask(
        task_id=str(uuid.uuid4()),
        source_database=source_db,
        target_database=target_db,
        source_table=source_table,
        target_table=target_table,
        key_columns=tuple(key_columns),
        update_column=update_column,
        extra_columns=tuple(extra_columns),
        sql_files=list(sql_file),
        sql_statements=list(sql_statement),
        validate_after_migration=validate,
        validation_threshold=threshold,
        description=description
    )
    
    task_id = agent.create_task(task)
    click.echo(f"✓ 已创建迁移任务: {task_id}")


@migration_cli.command()
@click.option("--task-id", required=True, help="任务 ID")
def execute(task_id):
    """执行迁移任务"""
    agent = MigrationAgent()
    progress = agent.execute_migration(task_id)
    
    if progress.status == MigrationStatus.COMPLETED:
        click.echo(f"✓ 迁移任务完成: {task_id}")
        click.echo(f"  进度: {progress.progress_percent:.1f}%")
    elif progress.status == MigrationStatus.FAILED:
        click.echo(f"✗ 迁移任务失败: {task_id}")
        click.echo(f"  错误: {progress.error}")
    else:
        click.echo(f"迁移任务状态: {progress.status.value}")


@migration_cli.command()
@click.option("--task-id", required=True, help="任务 ID")
def status(task_id):
    """查看迁移任务状态"""
    agent = MigrationAgent()
    progress = agent.get_progress(task_id)
    
    if not progress:
        click.echo(f"✗ 任务 {task_id} 不存在")
        return
    
    click.echo(f"任务 ID: {task_id}")
    click.echo(f"状态: {progress.status.value}")
    click.echo(f"进度: {progress.progress_percent:.1f}%")
    click.echo(f"当前步骤: {progress.current_step}")
    if progress.started_at:
        click.echo(f"开始时间: {progress.started_at}")
    if progress.completed_at:
        click.echo(f"完成时间: {progress.completed_at}")
    if progress.error:
        click.echo(f"错误: {progress.error}")


@migration_cli.command()
@click.option("--task-id", required=True, help="任务 ID")
def cancel(task_id):
    """取消迁移任务"""
    agent = MigrationAgent()
    if agent.cancel_task(task_id):
        click.echo(f"✓ 已取消任务: {task_id}")
    else:
        click.echo(f"✗ 无法取消任务: {task_id}")


@migration_cli.command()
@click.option("--source-db", required=True, help="源数据库连接字符串")
@click.option("--source-table", required=True, help="源表名")
@click.option("--target-db", required=True, help="目标数据库连接字符串")
@click.option("--target-table", required=True, help="目标表名")
@click.option("--key-columns", multiple=True, default=["id"], help="主键列")
@click.option("--threshold", type=float, default=0.0, help="验证阈值")
def validate(source_db, source_table, target_db, target_table, key_columns, threshold):
    """验证迁移结果"""
    from data_diff.migration.validator import MigrationValidator
    
    validator = MigrationValidator()
    result = validator.validate(
        source_database=source_db,
        source_table=source_table,
        target_database=target_db,
        target_table=target_table,
        key_columns=tuple(key_columns),
        threshold=threshold
    )
    
    if result["success"]:
        click.echo(f"✓ 验证通过")
        click.echo(f"  差异数量: {result['diff_count']}")
        click.echo(f"  差异百分比: {result['diff_percent']:.2f}%")
    else:
        click.echo(f"✗ 验证失败: {result.get('error')}")


if __name__ == "__main__":
    migration_cli()

